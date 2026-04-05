variable "project_name" {
  description = "Project name used for ECS naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
}

variable "service_name" {
  description = "Short ECS service name."
  type        = string
}

variable "cluster_name" {
  description = "ECS cluster name to create or reuse."
  type        = string
}

variable "create_cluster" {
  description = "Whether the module should create the ECS cluster."
  type        = bool
  default     = false
}

variable "enable_container_insights" {
  description = "Enable ECS Container Insights when creating the cluster."
  type        = bool
  default     = true
}

variable "image" {
  description = "Container image for the ECS task."
  type        = string
}

variable "cpu" {
  description = "Task CPU units."
  type        = number
}

variable "memory" {
  description = "Task memory in MiB."
  type        = number
}

variable "container_port" {
  description = "Container port exposed by the task. Set to null for background workers."
  type        = number
  default     = null
  nullable    = true
}

variable "desired_count" {
  description = "Initial desired ECS service count."
  type        = number
  default     = 1
}

variable "capacity_provider_strategy" {
  description = "Capacity provider strategy for the ECS service. When set, launch_type is not used."
  type = list(object({
    capacity_provider = string
    weight            = number
    base              = optional(number, 0)
  }))
  default = []
}

variable "subnet_ids" {
  description = "Subnet IDs for ECS service ENIs."
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC ID used for the ECS service security group."
  type        = string
}

variable "assign_public_ip" {
  description = "Assign public IPs to ECS tasks."
  type        = bool
  default     = false
}

variable "ingress_security_group_ids" {
  description = "Security groups allowed to reach the service container port."
  type        = list(string)
  default     = []
}

variable "ingress_cidr_blocks" {
  description = "CIDR blocks allowed to reach the service container port."
  type        = list(string)
  default     = []
}

variable "additional_security_group_ids" {
  description = "Additional security groups attached to the ECS service ENIs."
  type        = list(string)
  default     = []
}

variable "target_group_arn" {
  description = "Optional target group ARN for a load-balanced service."
  type        = string
  default     = null
  nullable    = true
}

variable "environment_variables" {
  description = "Plaintext environment variables passed to the container."
  type        = map(string)
  default     = {}
}

variable "secret_arns" {
  description = "Map of container secret names to Secrets Manager or SSM parameter ARNs."
  type        = map(string)
  default     = {}
}

variable "command" {
  description = "Optional container command override."
  type        = list(string)
  default     = []
}

variable "entrypoint" {
  description = "Optional container entrypoint override."
  type        = list(string)
  default     = []
}

variable "healthcheck_command" {
  description = "Optional container health check command."
  type        = list(string)
  default     = []
}

variable "healthcheck_interval" {
  description = "Container health check interval in seconds."
  type        = number
  default     = 30
}

variable "healthcheck_retries" {
  description = "Container health check retry count."
  type        = number
  default     = 3
}

variable "healthcheck_timeout" {
  description = "Container health check timeout in seconds."
  type        = number
  default     = 5
}

variable "healthcheck_start_period" {
  description = "Container health check start period in seconds."
  type        = number
  default     = 15
}

variable "task_family" {
  description = "Optional ECS task family override."
  type        = string
  default     = null
  nullable    = true
}

variable "create_log_group" {
  description = "Whether the module should create its CloudWatch log group."
  type        = bool
  default     = true
}

variable "log_group_name" {
  description = "Optional CloudWatch log group name override."
  type        = string
  default     = null
  nullable    = true
}

variable "log_retention_in_days" {
  description = "CloudWatch log retention for the service log group."
  type        = number
  default     = 30
}

variable "enable_execute_command" {
  description = "Enable ECS Exec for the service."
  type        = bool
  default     = true
}

variable "autoscaling_min_capacity" {
  description = "Minimum ECS desired count for auto scaling."
  type        = number
  default     = 1
}

variable "autoscaling_max_capacity" {
  description = "Maximum ECS desired count for auto scaling."
  type        = number
  default     = 4
}

variable "autoscaling_cpu_target" {
  description = "Target CPU utilization percentage for ECS target tracking."
  type        = number
  default     = 70
}

variable "s3_resource_arns" {
  description = "S3 ARNs the task role can access."
  type        = list(string)
  default     = []
}

variable "sqs_resource_arns" {
  description = "SQS ARNs the task role can access."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags applied to ECS resources."
  type        = map(string)
  default     = {}
}
