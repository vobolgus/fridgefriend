output "sns_topic_arn" {
  description = "SNS topic ARN used for infrastructure alerts."
  value       = aws_sns_topic.alerts.arn
}

output "log_group_names" {
  description = "Resolved log group names keyed by service name."
  value = var.create_log_groups ? {
    for service, log_group in aws_cloudwatch_log_group.ecs : service => log_group.name
  } : local.resolved_log_group_names
}

output "latency_alarm_arns" {
  description = "Map of ALB latency alarm ARNs keyed by service name."
  value = {
    for service, alarm in aws_cloudwatch_metric_alarm.latency_p95 : service => alarm.arn
  }
}

output "error_rate_alarm_arns" {
  description = "Map of ALB error-rate alarm ARNs keyed by service name."
  value = {
    for service, alarm in aws_cloudwatch_metric_alarm.error_rate : service => alarm.arn
  }
}

output "cpu_alarm_arns" {
  description = "Map of ECS CPU alarm ARNs keyed by ECS service name."
  value = {
    for service, alarm in aws_cloudwatch_metric_alarm.cpu_high : service => alarm.arn
  }
}
