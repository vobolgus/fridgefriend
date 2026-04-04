locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "Security group for ${local.name_prefix} ALB"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-alb-sg"
  })
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  description       = "Allow inbound HTTP"
}

resource "aws_vpc_security_group_ingress_rule" "https" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  description       = "Allow inbound HTTPS"
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound traffic"
}

resource "aws_lb" "this" {
  name               = substr(replace("${local.name_prefix}-alb", "_", "-"), 0, 32)
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids
  idle_timeout       = var.alb_idle_timeout

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-alb"
  })
}

resource "aws_lb_target_group" "backend" {
  name                 = substr(replace("${local.name_prefix}-be-tg", "_", "-"), 0, 32)
  port                 = var.backend_port
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = var.vpc_id
  deregistration_delay = var.backend_deregistration_delay

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    path                = var.backend_health_check_path
    matcher             = "200-399"
    protocol            = "HTTP"
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-backend-tg"
  })
}

resource "aws_lb_target_group" "dashboard" {
  name                 = substr(replace("${local.name_prefix}-dash-tg", "_", "-"), 0, 32)
  port                 = var.dashboard_port
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = var.vpc_id
  deregistration_delay = var.dashboard_deregistration_delay

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    path                = var.dashboard_health_check_path
    matcher             = "200-399"
    protocol            = "HTTP"
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-dashboard-tg"
  })
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = var.ssl_policy
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

resource "aws_lb_listener_rule" "dashboard" {
  listener_arn = aws_lb_listener.https.arn
  priority     = var.dashboard_rule_priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.dashboard.arn
  }

  condition {
    path_pattern {
      values = var.dashboard_path_patterns
    }
  }
}
