variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for cache subnet group"
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Security group ID of the application to allow inbound"
  type        = string
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t4g.micro"
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
