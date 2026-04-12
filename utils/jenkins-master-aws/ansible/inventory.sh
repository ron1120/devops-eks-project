#!/bin/bash
# Dynamic Ansible inventory — reads JENKINS_EIP from .env

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.env"

if [ "$1" == "--list" ]; then
  cat <<EOF
{
  "app": {
    "hosts": ["$JENKINS_EIP"],
    "vars": {
      "ansible_user": "ubuntu",
      "ansible_ssh_private_key_file": "~/aws_pems/awsFE.pem",
      "ansible_python_interpreter": "/usr/bin/python3"
    }
  }
}
EOF
elif [ "$1" == "--host" ]; then
  echo '{}'
fi
