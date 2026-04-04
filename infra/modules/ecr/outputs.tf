output "repository_urls" {
  description = "Map of repository URLs keyed by logical service name."
  value = {
    for name, repository in aws_ecr_repository.this : name => repository.repository_url
  }
}

output "repository_arns" {
  description = "Map of repository ARNs keyed by logical service name."
  value = {
    for name, repository in aws_ecr_repository.this : name => repository.arn
  }
}

output "backend_repository_url" {
  description = "Backend ECR repository URL."
  value       = aws_ecr_repository.this["backend"].repository_url
}

output "dashboard_repository_url" {
  description = "Dashboard ECR repository URL."
  value       = aws_ecr_repository.this["dashboard"].repository_url
}
