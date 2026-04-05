data "aws_region" "current" {}

locals {
  cluster_name = var.create_cluster ? aws_ecs_cluster.this[0].name : var.cluster_name
  cluster_id   = var.create_cluster ? aws_ecs_cluster.this[0].id : var.cluster_name
  family       = coalesce(var.task_family, "${var.project_name}-${var.environment}-${var.service_name}")
  log_group    = var.create_log_group ? aws_cloudwatch_log_group.service[0].name : coalesce(var.log_group_name, "/ecs/${var.project_name}/${var.environment}/${var.service_name}")

  container_definition = merge(
    {
      name      = var.service_name
      image     = var.image
      essential = true
      environment = [
        for name, value in var.environment_variables : {
          name  = name
          value = value
        }
      ]
      secrets = [
        for name, value_from in var.secret_arns : {
          name      = name
          valueFrom = value_from
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = local.log_group
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }
    },
    var.container_port == null ? {} : {
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
    },
    length(var.command) == 0 ? {} : {
      command = var.command
    },
    length(var.entrypoint) == 0 ? {} : {
      entryPoint = var.entrypoint
    },
    length(var.healthcheck_command) == 0 ? {} : {
      healthCheck = {
        command     = var.healthcheck_command
        interval    = var.healthcheck_interval
        retries     = var.healthcheck_retries
        timeout     = var.healthcheck_timeout
        startPeriod = var.healthcheck_start_period
      }
    }
  )
}

resource "aws_ecs_cluster" "this" {
  count = var.create_cluster ? 1 : 0

  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  tags = merge(var.tags, {
    Name = var.cluster_name
  })
}

resource "aws_cloudwatch_log_group" "service" {
  count = var.create_log_group ? 1 : 0

  name              = coalesce(var.log_group_name, "/ecs/${var.project_name}/${var.environment}/${var.service_name}")
  retention_in_days = var.log_retention_in_days

  tags = merge(var.tags, {
    Name = coalesce(var.log_group_name, "/ecs/${var.project_name}/${var.environment}/${var.service_name}")
  })
}

resource "aws_security_group" "service" {
  name        = "${var.project_name}-${var.environment}-${var.service_name}-sg"
  description = "Security group for ${var.service_name} ECS service"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-${var.service_name}-sg"
  })
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.service.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound traffic"
}

resource "aws_vpc_security_group_ingress_rule" "from_security_groups" {
  count = var.container_port == null ? 0 : length(var.ingress_security_group_ids)

  security_group_id            = aws_security_group.service.id
  referenced_security_group_id = var.ingress_security_group_ids[count.index]
  from_port                    = var.container_port
  to_port                      = var.container_port
  ip_protocol                  = "tcp"
  description                  = "Allow ingress from approved security group"
}

resource "aws_vpc_security_group_ingress_rule" "from_cidrs" {
  for_each = var.container_port == null ? toset([]) : toset(var.ingress_cidr_blocks)

  security_group_id = aws_security_group.service.id
  cidr_ipv4         = each.value
  from_port         = var.container_port
  to_port           = var.container_port
  ip_protocol       = "tcp"
  description       = "Allow ingress from approved CIDR"
}

resource "aws_ecs_task_definition" "this" {
  family                   = local.family
  cpu                      = tostring(var.cpu)
  memory                   = tostring(var.memory)
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn
  container_definitions    = jsonencode([local.container_definition])

  tags = merge(var.tags, {
    Name = local.family
  })
}

resource "aws_ecs_service" "this" {
  name                   = "${var.project_name}-${var.environment}-${var.service_name}"
  cluster                = local.cluster_id
  task_definition        = aws_ecs_task_definition.this.arn
  desired_count          = var.desired_count
  launch_type            = "FARGATE"
  platform_version       = "LATEST"
  enable_execute_command = var.enable_execute_command

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200
  propagate_tags                     = "SERVICE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = concat([aws_security_group.service.id], var.additional_security_group_ids)
    assign_public_ip = var.assign_public_ip
  }

  dynamic "load_balancer" {
    for_each = var.target_group_arn != null && var.container_port != null ? [var.target_group_arn] : []

    content {
      target_group_arn = load_balancer.value
      container_name   = var.service_name
      container_port   = var.container_port
    }
  }

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-${var.service_name}"
  })
}

resource "aws_appautoscaling_target" "service" {
  max_capacity       = var.autoscaling_max_capacity
  min_capacity       = var.autoscaling_min_capacity
  resource_id        = "service/${local.cluster_name}/${aws_ecs_service.this.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "${var.project_name}-${var.environment}-${var.service_name}-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.service.resource_id
  scalable_dimension = aws_appautoscaling_target.service.scalable_dimension
  service_namespace  = aws_appautoscaling_target.service.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = var.autoscaling_cpu_target
    scale_in_cooldown  = 120
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
