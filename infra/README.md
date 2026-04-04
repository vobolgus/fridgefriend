# FridgeFriend Terraform Infrastructure

Terraform configuration for the FridgeFriend AWS production stack.

## Architecture Overview

```text
                         Internet
                            |
                     +------+------+
                     |  Application |
                     | Load Balancer|
                     +---+------+---+
                         |      |
                   /api, /     /dashboard, /_stcore
                       |              |
             +---------+---+      +---+----------------+
             | ECS Fargate |      | ECS Fargate        |
             | backend API |      | dashboard          |
             +------+------+      +---------+----------+
                    |                        |
        +-----------+-----------+            |
        |                       |            |
  +-----+-----+           +-----+-----+      |
  | ECS worker|           | ECS beat  |      |
  +-----+-----+           +-----------+      |
        |                       |            |
        +-----------+-----------+------------+
                    |
      +-------------+-------------+-------------------+
      |             |             |                   |
   PostgreSQL     Redis         SQS             S3 + CloudFront
     (RDS)     (ElastiCache)   queues           assets / uploads
                    |
               CloudWatch + SNS alerts
```

## Modules

| Module | Purpose |
|---|---|
| `modules/vpc` | Base VPC, subnets, routing, and networking primitives |
| `modules/rds` | PostgreSQL database resources |
| `modules/elasticache` | Redis cache and Celery broker resources |
| `modules/s3_cdn` | S3 bucket and CloudFront distribution |
| `modules/sqs` | Async queues and dead-letter queues |
| `modules/secrets` | Secrets Manager / runtime secret resources |
| `modules/alb` | Public application load balancer, listeners, and target groups |
| `modules/ecr` | Container image repositories with scan-on-push and retention policy |
| `modules/ecs` | Reusable ECS Fargate service stack with IAM, logging, and auto-scaling |
| `modules/cloudwatch` | Alerting SNS topic, log groups, and service/ALB alarms |

## Production Environment

The production entrypoint lives in `infra/environments/prod/` and wires:

- networking (`vpc`)
- data plane (`rds`, `elasticache`, `s3_cdn`, `sqs`, `secrets`)
- edge and compute (`alb`, `ecr`, `ecs`)
- observability (`cloudwatch`)

Workloads provisioned in ECS:

- `backend` — FastAPI API behind the ALB
- `worker` — Celery worker using the backend image
- `beat` — Celery beat scheduler using the backend image
- `dashboard` — dashboard service behind the ALB

## Usage

From the repository root:

```bash
terraform -chdir=infra/environments/prod init
terraform -chdir=infra/environments/prod plan
terraform -chdir=infra/environments/prod apply
```

To inspect formatting before opening a PR:

```bash
terraform fmt -recursive infra
terraform -chdir=infra/environments/prod validate
```

## CI Validation

GitHub Actions validates Terraform changes on pushes and pull requests touching `infra/**`.

Checks performed:

- `terraform fmt -check -recursive`
- `terraform init -backend=false`
- `terraform validate`

## Cost Notes

This stack is production-oriented and not free-tier friendly.

Primary cost drivers:

- ECS Fargate services (`backend`, `worker`, `beat`, `dashboard`)
- RDS PostgreSQL instance
- ElastiCache Redis node
- NAT/data transfer, ALB hours, and CloudFront egress
- CloudWatch logs and alarms

Cost control ideas:

- keep worker and beat sizing conservative until queue volume grows
- shorten CloudWatch retention in lower environments
- use lifecycle policies on ECR and S3 to limit long-tail storage
- right-size RDS and Redis after observing production load
