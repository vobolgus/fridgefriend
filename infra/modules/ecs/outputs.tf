output "cluster_name" {
  description = "Name of the ECS cluster used by the service."
  value       = local.cluster_name
}

output "cluster_arn" {
  description = "ARN of the ECS cluster when created by this module."
  value       = try(aws_ecs_cluster.this[0].arn, null)
}

output "service_name" {
  description = "Name of the ECS service."
  value       = aws_ecs_service.this.name
}

output "service_arn" {
  description = "ARN of the ECS service."
  value       = aws_ecs_service.this.id
}

output "task_definition_arn" {
  description = "ARN of the ECS task definition."
  value       = aws_ecs_task_definition.this.arn
}

output "execution_role_arn" {
  description = "ARN of the ECS task execution role."
  value       = aws_iam_role.execution.arn
}

output "task_role_arn" {
  description = "ARN of the ECS task role."
  value       = aws_iam_role.task.arn
}

output "security_group_id" {
  description = "Security group ID attached to the ECS service."
  value       = aws_security_group.service.id
}

output "log_group_name" {
  description = "CloudWatch log group name used by the ECS service."
  value       = local.log_group
}
