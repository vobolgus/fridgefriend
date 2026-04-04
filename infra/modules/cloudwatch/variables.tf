variable "project_name" {
  description = "Project name used for alarm and log group naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
}

variable "service_names" {
  description = "Service names for log group creation."
  type        = list(string)
  default     = []
}

variable "create_log_groups" {
  description = "Whether the module should create ECS service log groups."
  type        = bool
  default     = true
}

variable "log_group_names" {
  description = "Optional explicit log group names keyed by service name."
  type        = map(string)
  default     = {}
}

variable "log_retention_in_days" {
  description = "CloudWatch log retention for created log groups."
  type        = number
  default     = 30
}

variable "alert_email_endpoints" {
  description = "Email endpoints subscribed to the SNS alert topic."
  type        = list(string)
  default     = []
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix used in Application Load Balancer metrics."
  type        = string
  default     = ""
}

variable "alb_target_group_arn_suffixes" {
  description = "Map of target group ARN suffixes keyed by logical service name."
  type        = map(string)
  default     = {}
}

variable "ecs_cluster_name" {
  description = "ECS cluster name used in ECS service alarms."
  type        = string
  default     = ""
}

variable "ecs_service_names" {
  description = "ECS service names used for CPU alarms."
  type        = list(string)
  default     = []
}

variable "latency_threshold_seconds" {
  description = "P95 target response time alarm threshold in seconds."
  type        = number
  default     = 5
}

variable "error_rate_threshold_percent" {
  description = "5XX error rate alarm threshold percentage."
  type        = number
  default     = 5
}

variable "cpu_threshold_percent" {
  description = "ECS CPU utilization alarm threshold percentage."
  type        = number
  default     = 80
}

variable "tags" {
  description = "Tags applied to CloudWatch and SNS resources."
  type        = map(string)
  default     = {}
}
