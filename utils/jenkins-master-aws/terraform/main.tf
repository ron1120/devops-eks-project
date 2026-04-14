terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_vpc" "existing" {
  count = var.existing_vpc_id != "" ? 1 : 0
  id    = var.existing_vpc_id
}

data "aws_internet_gateway" "existing" {
  count = var.existing_vpc_id != "" ? 1 : 0

  filter {
    name   = "attachment.vpc-id"
    values = [var.existing_vpc_id]
  }
}

locals {
  vpc_id              = var.existing_vpc_id != "" ? data.aws_vpc.existing[0].id : aws_vpc.main[0].id
  internet_gateway_id = var.existing_vpc_id != "" ? data.aws_internet_gateway.existing[0].id : aws_internet_gateway.igw[0].id
}

# VPC
resource "aws_vpc" "main" {
  count                = var.existing_vpc_id == "" ? 1 : 0
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Public Subnet
resource "aws_subnet" "public" {
  vpc_id                  = local.vpc_id
  cidr_block              = var.subnet_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  count  = var.existing_vpc_id == "" ? 1 : 0
  vpc_id = local.vpc_id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = local.vpc_id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = local.internet_gateway_id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security Group
resource "aws_security_group" "ec2_sg" {
  name        = "${var.project_name}-sg"
  description = "Allow SSH and outbound traffic"
  vpc_id      = local.vpc_id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "App on port 8080"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

# IAM Role for EC2 (Secrets Manager access)
data "aws_caller_identity" "current" {}

resource "aws_iam_role" "jenkins_ec2" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })

  tags = {
    Name = "${var.project_name}-ec2-role"
  }
}

resource "aws_iam_role_policy" "jenkins_secrets" {
  name = "${var.project_name}-secrets-policy"
  role = aws_iam_role.jenkins_ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.dockerhub_credentials.arn,
          aws_secretsmanager_secret.git_credentials.arn
        ]
      },
      {
        Effect   = "Allow"
        Action   = "secretsmanager:ListSecrets"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "jenkins" {
  name = "${var.project_name}-instance-profile"
  role = aws_iam_role.jenkins_ec2.name
}

# Secrets Manager
resource "aws_secretsmanager_secret" "dockerhub_credentials" {
  name                    = "DockerHubCredentials"
  description             = "Docker Hub username and password/token for Jenkins"
  recovery_window_in_days = 0

  tags = {
    Name                        = "${var.project_name}-dockerhub-creds"
    "jenkins:credentials:type"  = "usernamePassword"
  }
}

resource "aws_secretsmanager_secret" "git_credentials" {
  name                    = "RonGitUser"
  description             = "GitHub username and PAT for Jenkins"
  recovery_window_in_days = 0

  tags = {
    Name                        = "${var.project_name}-git-creds"
    "jenkins:credentials:type"  = "usernamePassword"
  }
}

# EC2 Instance
resource "aws_instance" "app" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  key_name                    = var.key_name
  iam_instance_profile        = aws_iam_instance_profile.jenkins.name

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 2
  }

  tags = {
    Name = "${var.project_name}-server"
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource tagging"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "key_name" {
  description = "Name of the SSH key pair"
  type        = string
}

variable "existing_vpc_id" {
  description = "Existing VPC ID to reuse instead of creating a new VPC"
  type        = string
  default     = ""
}

# Elastic IP — reuse existing if found by Name tag, otherwise create
data "aws_eips" "existing" {
  filter {
    name   = "tag:Name"
    values = ["${var.project_name}-eip"]
  }
}

locals {
  eip_exists        = length(data.aws_eips.existing.allocation_ids) > 0
  eip_allocation_id = local.eip_exists ? data.aws_eips.existing.allocation_ids[0] : aws_eip.jenkins[0].id
  eip_public_ip     = local.eip_exists ? data.aws_eips.existing.public_ips[0] : aws_eip.jenkins[0].public_ip
}

resource "aws_eip" "jenkins" {
  count  = local.eip_exists ? 0 : 1
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-eip"
  }
}

resource "aws_eip_association" "jenkins" {
  instance_id   = aws_instance.app.id
  allocation_id = local.eip_allocation_id
}

# Outputs
output "instance_public_ip" {
  value = local.eip_public_ip
}

output "vpc_id" {
  value = local.vpc_id
}

output "aws_region" {
  value = var.aws_region
}

