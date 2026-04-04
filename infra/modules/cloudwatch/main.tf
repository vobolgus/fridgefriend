locals {
  resolved_log_group_names = {
    for service in var.service_names :
    service => lookup(var.log_group_names, service, "/ecs/${var.project_name}/${var.environment}/${service}")
  }

  alb_target_groups_for_alarms = var.alb_arn_suffix == "" ? {} : var.alb_target_group_arn_suffixes
  ecs_services_for_alarms      = var.ecs_cluster_name == "" ? toset([]) : toset(var.ecs_service_names)
}

resource "aws_cloudwatch_log_group" "ecs" {
  for_each = var.create_log_groups ? local.resolved_log_group_names : {}

  name              = each.value
  retention_in_days = var.log_retention_in_days

  tags = merge(var.tags, {
    Name = each.value
  })
}

resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-alerts"
  })
}

resource "aws_sns_topic_subscription" "email" {
  for_each = toset(var.alert_email_endpoints)

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = each.value
}

resource "aws_cloudwatch_metric_alarm" "latency_p95" {
  for_each = local.alb_target_groups_for_alarms

  alarm_name          = "${var.project_name}-${var.environment}-${each.key}-latency-p95"
  alarm_description   = "ALB target response time p95 is above ${var.latency_threshold_seconds}s for ${each.key}."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = var.latency_threshold_seconds
  treat_missing_data  = "notBreaching"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "TargetResponseTime"
  extended_statistic  = "p95"
  period              = 60

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = each.value
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "error_rate" {
  for_each = local.alb_target_groups_for_alarms

  alarm_name          = "${var.project_name}-${var.environment}-${each.key}-error-rate"
  alarm_description   = "ALB 5XX error rate is above ${var.error_rate_threshold_percent}% for ${each.key}."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = var.error_rate_threshold_percent
  treat_missing_data  = "notBreaching"

  metric_query {
    id = "errors"

    metric {
      namespace   = "AWS/ApplicationELB"
      metric_name = "HTTPCode_Target_5XX_Count"
      period      = 60
      stat        = "Sum"

      dimensions = {
        LoadBalancer = var.alb_arn_suffix
        TargetGroup  = each.value
      }
    }
  }

  metric_query {
    id = "requests"

    metric {
      namespace   = "AWS/ApplicationELB"
      metric_name = "RequestCount"
      period      = 60
      stat        = "Sum"

      dimensions = {
        LoadBalancer = var.alb_arn_suffix
        TargetGroup  = each.value
      }
    }
  }

  metric_query {
    id          = "error_rate"
    expression  = "IF(requests > 0, (errors / requests) * 100, 0)"
    label       = "Error rate percent"
    return_data = true
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  for_each = local.ecs_services_for_alarms

  alarm_name          = "${var.project_name}-${var.environment}-${each.value}-cpu-high"
  alarm_description   = "ECS service CPU is above ${var.cpu_threshold_percent}% for ${each.value}."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = var.cpu_threshold_percent
  treat_missing_data  = "notBreaching"
  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 60

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = each.value
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}
