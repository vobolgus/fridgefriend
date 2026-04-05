output "alb_dns_name" {
  description = "Public DNS name of the production ALB."
  value       = module.alb.dns_name
}

output "rds_endpoint" {
  description = "Production PostgreSQL endpoint."
  value       = module.rds.endpoint
}

output "redis_endpoint" {
  description = "Production Redis endpoint."
  value       = module.elasticache.primary_endpoint
}

output "s3_bucket" {
  description = "Primary S3 bucket name for assets or uploads."
  value       = module.s3_cdn.bucket_name
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain name."
  value       = module.s3_cdn.cloudfront_domain
}

output "backend_ecr_url" {
  description = "Backend ECR repository URL."
  value       = module.ecr.backend_repository_url
}

output "dashboard_ecr_url" {
  description = "Dashboard ECR repository URL."
  value       = module.ecr.dashboard_repository_url
}
