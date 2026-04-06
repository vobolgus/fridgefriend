data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  azs         = length(var.availability_zones) > 0 ? var.availability_zones : slice(data.aws_availability_zones.available.names, 0, 3)

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })

  default_s3_bucket_arn = try(module.s3_cdn.bucket_arn, null)

  backend_base_environment = {
    APP_ENV              = var.environment
    AWS_REGION           = var.aws_region
    DEBUG                = "false"
    AUTH_MOCK            = "false"
    FIREBASE_PROJECT_ID  = "fridge-friend-c5a88"
    BARCODE_API_SOURCE   = "openfoodfacts"
    RECIPE_SOURCE        = "mock"
    STORAGE_BACKEND      = "s3"
    S3_BUCKET            = module.s3_cdn.bucket_name
    S3_ENDPOINT_URL      = ""
    SQS_QUEUE_URL        = module.sqs.queue_url
    CDN_DOMAIN           = module.s3_cdn.cloudfront_domain
    FCM_ENABLED          = "true"
    SENTRY_ENVIRONMENT   = var.environment
    IDEMPOTENCY_BACKEND  = "redis"
    PHOTO_PARSER_BACKEND      = "llm"
    PHOTO_PARSER_ALLOWED_UIDS = "TLizIBIqc4OgADKKHXNJR6zEkVg2"
    OPENSEARCH_URL       = ""
    OPENSEARCH_INDEX     = "recipes"
  }

  backend_secret_arns = {
    DATABASE_URL               = module.secrets.secret_arns["database-url"]
    REDIS_URL                  = module.secrets.secret_arns["redis-url"]
    LLM_API_KEY                = module.secrets.secret_arns["llm-api-key"]
    FIREBASE_CREDENTIALS_JSON  = module.secrets.secret_arns["firebase-credentials"]
  }

  dashboard_base_environment = {
    APP_ENV        = var.environment
    AWS_REGION     = var.aws_region
    API_BASE_URL   = "https://${module.alb.dns_name}"
    CDN_DOMAIN     = module.s3_cdn.cloudfront_domain
    DASHBOARD_PORT = "8501"
  }

  shared_s3_resource_arns = length(var.task_role_s3_arns) > 0 ? var.task_role_s3_arns : (
    local.default_s3_bucket_arn == null ? [] : [
      local.default_s3_bucket_arn,
      "${local.default_s3_bucket_arn}/*"
    ]
  )

  shared_sqs_resource_arns = length(var.task_role_sqs_arns) > 0 ? var.task_role_sqs_arns : [
    module.sqs.queue_arn,
    module.sqs.dlq_arn
  ]
}

module "vpc" {
  source = "../../modules/vpc"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = local.azs
  use_fck_nat        = var.use_fck_nat
  enable_s3_endpoint = var.enable_s3_endpoint
  tags               = local.common_tags
}

module "secrets" {
  source = "../../modules/secrets"

  project_name = var.project_name
  environment  = var.environment
  tags         = local.common_tags
}

module "ecr" {
  source = "../../modules/ecr"

  tags = local.common_tags
}

module "s3_cdn" {
  source = "../../modules/s3_cdn"

  project_name = var.project_name
  environment  = var.environment
  tags         = local.common_tags
}

module "sqs" {
  source = "../../modules/sqs"

  project_name = var.project_name
  environment  = var.environment
  tags         = local.common_tags
}

module "alb" {
  source = "../../modules/alb"

  project_name            = var.project_name
  environment             = var.environment
  vpc_id                  = module.vpc.vpc_id
  public_subnet_ids       = module.vpc.public_subnet_ids
  acm_certificate_arn     = var.acm_cert_arn
  dashboard_path_patterns = var.dashboard_path_patterns
  tags                    = local.common_tags
}

module "ecs_backend" {
  source = "../../modules/ecs"

  project_name               = var.project_name
  environment                = var.environment
  service_name               = "backend"
  cluster_name               = "${local.name_prefix}-cluster"
  create_cluster             = true
  image                      = var.backend_container_image
  cpu                        = var.backend_cpu
  memory                     = var.backend_memory
  container_port             = 8000
  desired_count              = var.backend_desired_count
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.private_subnet_ids
  ingress_security_group_ids = [module.alb.security_group_id]
  target_group_arn           = module.alb.backend_target_group_arn
  environment_variables      = merge(local.backend_base_environment, { SERVICE_NAME = "backend", SERVICE_PORT = "8000" }, var.backend_environment_variables)
  secret_arns                = merge(local.backend_secret_arns, var.backend_secret_arns)
  s3_resource_arns           = local.shared_s3_resource_arns
  sqs_resource_arns          = local.shared_sqs_resource_arns
  healthcheck_command        = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  tags                       = local.common_tags
}

module "rds" {
  source = "../../modules/rds"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  app_security_group_id = module.ecs_backend.security_group_id
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password
  instance_class        = var.db_instance_class

  backup_retention_period      = var.rds_backup_retention_period
  deletion_protection          = var.rds_deletion_protection
  skip_final_snapshot          = var.rds_skip_final_snapshot
  performance_insights_enabled = var.rds_performance_insights_enabled

  tags = local.common_tags
}

module "elasticache" {
  source = "../../modules/elasticache"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  app_security_group_id = module.ecs_backend.security_group_id
  node_type             = var.redis_node_type
  tags                  = local.common_tags
}

module "ecs_worker" {
  source = "../../modules/ecs"

  project_name  = var.project_name
  environment   = var.environment
  service_name  = "worker"
  cluster_name  = module.ecs_backend.cluster_name
  image         = var.backend_container_image
  cpu           = var.worker_cpu
  memory        = var.worker_memory
  desired_count = var.worker_desired_count
  capacity_provider_strategy = [
    { capacity_provider = "FARGATE_SPOT", weight = 1, base = 1 }
  ]
  vpc_id                = module.vpc.vpc_id
  subnet_ids            = module.vpc.private_subnet_ids
  environment_variables = merge(local.backend_base_environment, { SERVICE_NAME = "worker" }, var.worker_environment_variables)
  secret_arns           = merge(local.backend_secret_arns, var.worker_secret_arns)
  command               = ["celery", "-A", "app.worker", "worker", "-B", "--loglevel=INFO"]
  s3_resource_arns      = local.shared_s3_resource_arns
  sqs_resource_arns     = local.shared_sqs_resource_arns
  tags                  = local.common_tags
}

module "ecs_dashboard" {
  source = "../../modules/ecs"

  project_name               = var.project_name
  environment                = var.environment
  service_name               = "dashboard"
  cluster_name               = module.ecs_backend.cluster_name
  image                      = var.dashboard_container_image
  cpu                        = var.dashboard_cpu
  memory                     = var.dashboard_memory
  container_port             = 8501
  desired_count              = var.dashboard_desired_count
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.private_subnet_ids
  ingress_security_group_ids = [module.alb.security_group_id]
  target_group_arn           = module.alb.dashboard_target_group_arn
  environment_variables      = merge(local.dashboard_base_environment, var.dashboard_environment_variables)
  secret_arns                = var.dashboard_secret_arns
  healthcheck_command        = ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"]
  s3_resource_arns           = local.shared_s3_resource_arns
  sqs_resource_arns          = local.shared_sqs_resource_arns
  tags                       = local.common_tags
}

module "cloudwatch" {
  source = "../../modules/cloudwatch"

  project_name      = var.project_name
  environment       = var.environment
  service_names     = ["backend", "worker", "dashboard"]
  create_log_groups = false
  log_group_names = {
    backend   = module.ecs_backend.log_group_name
    worker    = module.ecs_worker.log_group_name
    dashboard = module.ecs_dashboard.log_group_name
  }
  alert_email_endpoints = var.alert_email_endpoints
  alb_arn_suffix        = module.alb.alb_arn_suffix
  alb_target_group_arn_suffixes = {
    backend   = module.alb.backend_target_group_arn_suffix
    dashboard = module.alb.dashboard_target_group_arn_suffix
  }
  ecs_cluster_name = "${local.name_prefix}-cluster"
  ecs_service_names = [
    "${local.name_prefix}-backend",
    "${local.name_prefix}-worker",
    "${local.name_prefix}-dashboard"
  ]
  tags = local.common_tags
}
