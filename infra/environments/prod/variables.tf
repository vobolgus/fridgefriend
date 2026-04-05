variable "project_name" {
  description = "Project name used for naming AWS resources."
  type        = string
}

variable "environment" {
  description = "Environment name used for naming and tagging."
  type        = string
}

variable "aws_region" {
  description = "AWS region for the production environment."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the production VPC."
  type        = string
}

variable "availability_zones" {
  description = "Optional explicit availability zones. Defaults to the first three in the configured region."
  type        = list(string)
  default     = []
}

variable "db_instance_class" {
  description = "RDS instance class for PostgreSQL."
  type        = string
}

variable "db_name" {
  description = "Primary PostgreSQL database name."
  type        = string
  default     = "fridgefriend"
}

variable "db_username" {
  description = "Master username for PostgreSQL."
  type        = string
  default     = "fridgefriend"
}

variable "db_password" {
  description = "Master password for PostgreSQL. Pass via TF_VAR_db_password or -var flag. Never commit."
  type        = string
  sensitive   = true
}

variable "rds_backup_retention_period" {
  description = "Days to retain RDS automated backups. Set to 0 for free-tier."
  type        = number
  default     = 7
}

variable "rds_deletion_protection" {
  description = "Enable RDS deletion protection."
  type        = bool
  default     = true
}

variable "rds_skip_final_snapshot" {
  description = "Skip final snapshot on RDS deletion."
  type        = bool
  default     = false
}

variable "rds_performance_insights_enabled" {
  description = "Enable RDS Performance Insights."
  type        = bool
  default     = true
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type."
  type        = string
}

variable "acm_cert_arn" {
  description = "ACM certificate ARN for the public ALB HTTPS listener."
  type        = string
}

variable "backend_container_image" {
  description = "Container image URI for the backend API and worker workloads."
  type        = string
}

variable "dashboard_container_image" {
  description = "Container image URI for the dashboard service."
  type        = string
}

variable "backend_cpu" {
  description = "Backend ECS task CPU units."
  type        = number
}

variable "backend_memory" {
  description = "Backend ECS task memory in MiB."
  type        = number
}

variable "worker_cpu" {
  description = "Worker and beat ECS task CPU units."
  type        = number
}

variable "worker_memory" {
  description = "Worker and beat ECS task memory in MiB."
  type        = number
}

variable "dashboard_cpu" {
  description = "Dashboard ECS task CPU units."
  type        = number
}

variable "dashboard_memory" {
  description = "Dashboard ECS task memory in MiB."
  type        = number
}

variable "backend_desired_count" {
  description = "Desired count for the backend ECS service."
  type        = number
  default     = 2
}

variable "worker_desired_count" {
  description = "Desired count for the worker ECS service."
  type        = number
  default     = 1
}

variable "beat_desired_count" {
  description = "Desired count for the beat ECS service."
  type        = number
  default     = 1
}

variable "dashboard_desired_count" {
  description = "Desired count for the dashboard ECS service."
  type        = number
  default     = 1
}

variable "alert_email_endpoints" {
  description = "Optional email addresses subscribed to infrastructure alerts."
  type        = list(string)
  default     = []
}

variable "dashboard_path_patterns" {
  description = "ALB path patterns that should route traffic to the dashboard target group."
  type        = list(string)
  default     = ["/dashboard*", "/_stcore/*"]
}

variable "backend_environment_variables" {
  description = "Additional plaintext environment variables for the backend service."
  type        = map(string)
  default     = {}
}

variable "worker_environment_variables" {
  description = "Additional plaintext environment variables for the worker service."
  type        = map(string)
  default     = {}
}

variable "beat_environment_variables" {
  description = "Additional plaintext environment variables for the beat service."
  type        = map(string)
  default     = {}
}

variable "dashboard_environment_variables" {
  description = "Additional plaintext environment variables for the dashboard service."
  type        = map(string)
  default     = {}
}

variable "backend_secret_arns" {
  description = "Container secret ARNs for the backend service."
  type        = map(string)
  default     = {}
}

variable "worker_secret_arns" {
  description = "Container secret ARNs for the worker service."
  type        = map(string)
  default     = {}
}

variable "beat_secret_arns" {
  description = "Container secret ARNs for the beat service."
  type        = map(string)
  default     = {}
}

variable "dashboard_secret_arns" {
  description = "Container secret ARNs for the dashboard service."
  type        = map(string)
  default     = {}
}

variable "task_role_s3_arns" {
  description = "S3 ARNs allowed for ECS task roles."
  type        = list(string)
  default     = []
}

variable "task_role_sqs_arns" {
  description = "SQS ARNs allowed for ECS task roles."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Additional tags applied to all production resources."
  type        = map(string)
  default     = {}
}
