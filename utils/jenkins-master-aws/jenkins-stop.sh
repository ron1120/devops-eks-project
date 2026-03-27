# Stop Jenkins Master on AWS EC2 instance
#!/bin/bash

# Stop the instance using AWS CLI
aws ec2 stop-instances --region "us-east-1" --instance-ids "$INSTANCE_ID"

