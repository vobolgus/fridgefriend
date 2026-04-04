output "primary_endpoint" {
  description = "Primary endpoint address for Redis"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "port" {
  description = "Redis port"
  value       = 6379
}

output "security_group_id" {
  description = "Security group ID of the Redis cluster"
  value       = aws_security_group.cache.id
}
