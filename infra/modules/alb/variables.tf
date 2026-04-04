variable "project_name" {
  description = "Project name used for naming ALB resources."
  type        = string
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the ALB and target groups will be created."
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs used by the ALB."
  type        = list(string)
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for the HTTPS listener."
  type        = string
}

variable "backend_port" {
  description = "Backend target group port."
  type        = number
  default     = 8000
}

variable "dashboard_port" {
  description = "Dashboard target group port."
  type        = number
  default     = 8501
}

variable "backend_health_check_path" {
  description = "Backend target group health check path."
  type        = string
  default     = "/health"
}

variable "dashboard_health_check_path" {
  description = "Dashboard target group health check path."
  type        = string
  default     = "/_stcore/health"
}

variable "dashboard_path_patterns" {
  description = "Path patterns routed to the dashboard target group."
  type        = list(string)
  default     = ["/dashboard*", "/_stcore/*"]
}

variable "dashboard_rule_priority" {
  description = "Listener rule priority for dashboard routing."
  type        = number
  default     = 10
}

variable "alb_idle_timeout" {
  description = "ALB idle timeout in seconds."
  type        = number
  default     = 60
}

variable "backend_deregistration_delay" {
  description = "Deregistration delay for the backend target group."
  type        = number
  default     = 30
}

variable "dashboard_deregistration_delay" {
  description = "Deregistration delay for the dashboard target group."
  type        = number
  default     = 30
}

variable "ssl_policy" {
  description = "SSL policy applied to the HTTPS listener."
  type        = string
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"
}

variable "tags" {
  description = "Tags applied to ALB resources."
  type        = map(string)
  default     = {}
}
