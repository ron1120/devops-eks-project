#!/bin/bash

# Dynamically fetch the correct region from Terraform to prevent endpoint errors
export AWS_DEFAULT_REGION=$(cd ../terraform && terraform output -raw aws_region)

INSTANCE_IP=$(cd ../terraform && terraform output -raw instance_public_ip)
echo "Instance IP: $INSTANCE_IP"

VPC_ID=$(cd ../terraform && terraform output -raw vpc_id)
echo "VPC ID: $VPC_ID"

INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=ip-address,Values=$INSTANCE_IP" --query "Reservations[].Instances[].InstanceId" --output text)         
echo "Instance ID: $INSTANCE_ID"
