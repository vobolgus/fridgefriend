output "alb_arn" {
  description = "ARN of the application load balancer."
  value       = aws_lb.this.arn
}

output "alb_arn_suffix" {
  description = "ARN suffix of the application load balancer for CloudWatch metrics."
  value       = aws_lb.this.arn_suffix
}

output "dns_name" {
  description = "DNS name of the application load balancer."
  value       = aws_lb.this.dns_name
}

output "zone_id" {
  description = "Route53 zone ID of the application load balancer."
  value       = aws_lb.this.zone_id
}

output "security_group_id" {
  description = "Security group ID attached to the ALB."
  value       = aws_security_group.alb.id
}

output "https_listener_arn" {
  description = "ARN of the HTTPS listener."
  value       = aws_lb_listener.https.arn
}

output "backend_target_group_arn" {
  description = "Backend target group ARN."
  value       = aws_lb_target_group.backend.arn
}

output "backend_target_group_arn_suffix" {
  description = "Backend target group ARN suffix for CloudWatch metrics."
  value       = aws_lb_target_group.backend.arn_suffix
}

output "dashboard_target_group_arn" {
  description = "Dashboard target group ARN."
  value       = aws_lb_target_group.dashboard.arn
}

output "dashboard_target_group_arn_suffix" {
  description = "Dashboard target group ARN suffix for CloudWatch metrics."
  value       = aws_lb_target_group.dashboard.arn_suffix
}
