variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "enable_multi_az_nat" {
  description = "Deploy one NAT gateway per AZ (true) or single NAT (false) for cost savings"
  type        = bool
  default     = false
}

variable "use_fck_nat" {
  description = "Replace managed NAT Gateway with fck-nat instance for cost savings (~$32/mo → ~$3/mo)."
  type        = bool
  default     = false
}

variable "fck_nat_instance_type" {
  description = "Instance type for fck-nat NAT instance."
  type        = string
  default     = "t4g.micro"
}

variable "enable_s3_endpoint" {
  description = "Create an S3 Gateway VPC endpoint to avoid NAT charges for S3 traffic."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}
