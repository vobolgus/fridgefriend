project_name                     = "fridgefriend"
environment                      = "production"
aws_region                       = "us-east-1"
vpc_cidr                         = "10.0.0.0/16"
use_fck_nat                      = true
enable_s3_endpoint               = true
db_instance_class                = "db.t3.micro"
rds_backup_retention_period      = 0
rds_deletion_protection          = false
rds_skip_final_snapshot          = true
rds_performance_insights_enabled = false
redis_node_type                  = "cache.t4g.micro"
acm_cert_arn                     = "arn:aws:acm:us-east-1:490346182218:certificate/721e331c-9673-4531-ad50-91ecd7f98fa0"
backend_container_image          = "490346182218.dkr.ecr.us-east-1.amazonaws.com/fridgefriend-backend:latest"
dashboard_container_image        = "490346182218.dkr.ecr.us-east-1.amazonaws.com/fridgefriend-dashboard:latest"
backend_cpu                      = 512
backend_memory                   = 1024
# Existing backend service uses ignore_changes for desired_count; run:
# aws ecs update-service --cluster fridgefriend-production-cluster --service fridgefriend-production-backend --desired-count 1
backend_desired_count = 1
worker_cpu            = 256
worker_memory         = 512
dashboard_cpu         = 256
dashboard_memory      = 512
