variable "backend_repository_name" {
  description = "Name of the backend ECR repository."
  type        = string
  default     = "fridgefriend-backend"
}

variable "dashboard_repository_name" {
  description = "Name of the dashboard ECR repository."
  type        = string
  default     = "fridgefriend-dashboard"
}

variable "tags" {
  description = "Tags applied to ECR repositories."
  type        = map(string)
  default     = {}
}
