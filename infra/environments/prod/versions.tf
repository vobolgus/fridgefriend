terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }

  # backend "s3" {
  #   bucket         = "replace-with-terraform-state-bucket"
  #   key            = "fridgefriend/production/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "replace-with-terraform-locks-table"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
}
