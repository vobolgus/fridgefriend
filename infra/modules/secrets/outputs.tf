output "secret_arns" {
  description = "Map of secret name to ARN"
  value       = { for k, v in aws_secretsmanager_secret.app_secrets : k => v.arn }
}

output "kms_key_arn" {
  description = "ARN of the KMS key used for encryption"
  value       = aws_kms_key.secrets.arn
}

output "secrets_read_policy_json" {
  description = "IAM policy JSON granting read access to all secrets"
  value       = data.aws_iam_policy_document.secrets_read.json
}
