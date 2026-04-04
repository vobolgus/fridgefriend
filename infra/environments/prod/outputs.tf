output "alb_dns_name" {
  description = "Public DNS name of the production ALB."
  value       = module.alb.dns_name
}

output "rds_endpoint" {
  description = "Production PostgreSQL endpoint."
  value       = try(module.rds.endpoint, try(module.rds.address, null))
}

output "redis_endpoint" {
  description = "Production Redis endpoint."
  value       = try(module.elasticache.primary_endpoint_address, try(module.elasticache.endpoint, null))
}

output "s3_bucket" {
  description = "Primary S3 bucket name for assets or uploads."
  value       = try(module.s3_cdn.bucket_name, try(module.s3_cdn.s3_bucket_name, null))
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain name."
  value       = try(module.s3_cdn.cloudfront_domain_name, try(module.s3_cdn.domain_name, null))
}

output "backend_ecr_url" {
  description = "Backend ECR repository URL."
  value       = module.ecr.backend_repository_url
}

output "dashboard_ecr_url" {
  description = "Dashboard ECR repository URL."
  value       = module.ecr.dashboard_repository_url
}
