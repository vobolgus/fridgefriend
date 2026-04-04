locals {
  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })

  secret_names = [
    "database-url",
    "redis-url",
    "firebase-credentials",
    "spoonacular-api-key",
    "sentry-dsn",
    "amplitude-api-key",
  ]
}

resource "aws_kms_key" "secrets" {
  description             = "KMS key for ${var.project_name} ${var.environment} secrets"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-secrets-key" })
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/${var.project_name}-${var.environment}-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

resource "aws_secretsmanager_secret" "app_secrets" {
  for_each = toset(local.secret_names)

  name        = "${var.project_name}/${var.environment}/${each.value}"
  description = "${each.value} for ${var.project_name} ${var.environment}"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-${each.value}" })
}

data "aws_iam_policy_document" "secrets_read" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [for s in aws_secretsmanager_secret.app_secrets : s.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
    ]
    resources = [aws_kms_key.secrets.arn]
  }
}
