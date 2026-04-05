data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "execution_access" {
  statement {
    sid    = "ReadRuntimeSecrets"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "ssm:GetParameter",
      "ssm:GetParameters",
      "kms:Decrypt"
    ]
    resources = ["*"]
  }

  statement {
    sid    = "WriteContainerLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }
}

data "aws_iam_policy_document" "task_access" {
  dynamic "statement" {
    for_each = length(var.s3_resource_arns) > 0 ? [1] : []

    content {
      sid    = "S3Access"
      effect = "Allow"
      actions = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ]
      resources = var.s3_resource_arns
    }
  }

  dynamic "statement" {
    for_each = length(var.sqs_resource_arns) > 0 ? [1] : []

    content {
      sid    = "SQSAccess"
      effect = "Allow"
      actions = [
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:ChangeMessageVisibility",
        "sqs:SendMessage"
      ]
      resources = var.sqs_resource_arns
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = "${var.project_name}-${var.environment}-${var.service_name}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-${var.service_name}-execution-role"
  })
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_access" {
  name   = "${var.project_name}-${var.environment}-${var.service_name}-execution-access"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.execution_access.json
}

resource "aws_iam_role" "task" {
  name               = "${var.project_name}-${var.environment}-${var.service_name}-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-${var.service_name}-task-role"
  })
}

resource "aws_iam_role_policy" "task_access" {
  name   = "${var.project_name}-${var.environment}-${var.service_name}-task-access"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.task_access.json
}
