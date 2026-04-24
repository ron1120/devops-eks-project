#!/usr/bin/env bash
# Tear down the EKS stack safely.
#
# Terraform doesn't know about AWS resources created by Kubernetes
# (Service type=LoadBalancer -> ELB + auto SG + ENI, PVCs -> EBS volumes).
# Leaving those around blocks `terraform destroy` with DependencyViolation
# on the VPC / subnets / IGW. This script removes them first, then runs
# terraform destroy.
#
# Order:
#   1. Uninstall Helm releases that create ELBs (kube-prom, loki).
#   2. Delete any LoadBalancer Services across all namespaces.
#   3. Delete the `monitoring` namespace (drops PVCs -> EBS volumes).
#   4. Belt-and-suspenders: delete any remaining classic ELBs / ALBs / NLBs
#      inside the EKS VPC and their auto-created k8s-elb-* SGs.
#   5. terraform destroy -auto-approve.
#
# Usage:
#   configure-env/destroy-eks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TF_DIR="${REPO_ROOT}/terraform/devops-eks-cluster"
ENV_FILE="${SCRIPT_DIR}/.env"

AWS_REGION="${AWS_REGION:-us-east-1}"
EKS_CLUSTER_NAME="${EKS_CLUSTER_NAME:-devops-eks-cluster}"
VPC_NAME_TAG="${VPC_NAME_TAG:-devops-eks-project-eks-vpc}"

if [ -f "$ENV_FILE" ]; then
  # shellcheck source=/dev/null
  set -a && source "$ENV_FILE" && set +a
fi

export AWS_PAGER=

echo "[destroy-eks] region=${AWS_REGION}  cluster=${EKS_CLUSTER_NAME}"

# ── 0. Preflight: fail fast on bad AWS credentials ──────────────────────────
# A 64-char secret or a stale/expired key produces dozens of confusing
# AuthFailure / SignatureDoesNotMatch errors further down. Stop early.
if [ -n "${AWS_SECRET_ACCESS_KEY:-}" ] && [ "${#AWS_SECRET_ACCESS_KEY}" -ne 40 ]; then
  echo "[destroy-eks] ERROR: AWS_SECRET_ACCESS_KEY is ${#AWS_SECRET_ACCESS_KEY} chars; expected 40." >&2
  echo "             Fix configure-env/.env or unset it and use 'aws configure' / AWS_PROFILE." >&2
  exit 1
fi
if ! aws sts get-caller-identity --region "$AWS_REGION" >/dev/null 2>&1; then
  echo "[destroy-eks] ERROR: aws sts get-caller-identity failed — credentials are invalid." >&2
  echo "             Try:   AWS_PAGER= aws sts get-caller-identity --region ${AWS_REGION}" >&2
  exit 1
fi

# ── 1. Refresh kubeconfig (best-effort; cluster may already be gone) ─────────
if aws eks describe-cluster \
     --name "$EKS_CLUSTER_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
  echo "[destroy-eks] refreshing kubeconfig"
  aws eks update-kubeconfig \
    --name "$EKS_CLUSTER_NAME" --region "$AWS_REGION" >/dev/null
  CLUSTER_ALIVE=1
else
  echo "[destroy-eks] EKS cluster not found — skipping kubectl/helm cleanup"
  CLUSTER_ALIVE=0
fi

# ── 2. Helm + kubectl cleanup (only if the cluster still responds) ───────────
if [ "$CLUSTER_ALIVE" = "1" ]; then
  if command -v helm >/dev/null 2>&1; then
    echo "[destroy-eks] helm uninstall kube-prom loki (ignoring errors)"
    helm uninstall kube-prom -n monitoring 2>/dev/null || true
    helm uninstall loki      -n monitoring 2>/dev/null || true
  fi

  echo "[destroy-eks] deleting any LoadBalancer Services"
  kubectl delete svc --all-namespaces \
    --field-selector spec.type=LoadBalancer \
    --ignore-not-found --wait=true || true

  echo "[destroy-eks] deleting 'monitoring' namespace (PVCs -> EBS)"
  kubectl delete ns monitoring --ignore-not-found --wait=true || true
fi

# ── 3. Find VPC by Name tag (set by Terraform) ───────────────────────────────
VPC_ID="$(aws ec2 describe-vpcs --region "$AWS_REGION" \
  --filters "Name=tag:Name,Values=${VPC_NAME_TAG}" \
  --query 'Vpcs[].VpcId' --output text)"

if [ -z "$VPC_ID" ] || [ "$VPC_ID" = "None" ]; then
  echo "[destroy-eks] VPC tagged Name=${VPC_NAME_TAG} not found — nothing extra to clean"
else
  echo "[destroy-eks] scanning VPC ${VPC_ID} for orphan LB resources"

  # Classic ELBs
  mapfile -t CLB_NAMES < <(aws elb describe-load-balancers --region "$AWS_REGION" \
    --query "LoadBalancerDescriptions[?VPCId=='${VPC_ID}'].LoadBalancerName" \
    --output text | tr '\t' '\n' | sed '/^$/d')
  for LB in "${CLB_NAMES[@]}"; do
    echo "[destroy-eks] deleting classic ELB: $LB"
    aws elb delete-load-balancer --region "$AWS_REGION" --load-balancer-name "$LB" || true
  done

  # ALBs / NLBs
  mapfile -t LBV2_ARNS < <(aws elbv2 describe-load-balancers --region "$AWS_REGION" \
    --query "LoadBalancers[?VpcId=='${VPC_ID}'].LoadBalancerArn" \
    --output text | tr '\t' '\n' | sed '/^$/d')
  for ARN in "${LBV2_ARNS[@]}"; do
    echo "[destroy-eks] deleting v2 LB: $ARN"
    aws elbv2 delete-load-balancer --region "$AWS_REGION" --load-balancer-arn "$ARN" || true
  done

  # Wait for ELB-owned ENIs to disappear (up to 2 minutes)
  if [ "${#CLB_NAMES[@]}" -gt 0 ] || [ "${#LBV2_ARNS[@]}" -gt 0 ]; then
    echo "[destroy-eks] waiting for LB ENIs to release"
    for _ in $(seq 1 24); do
      COUNT=$(aws ec2 describe-network-interfaces --region "$AWS_REGION" \
        --filters "Name=vpc-id,Values=${VPC_ID}" \
                  "Name=description,Values=ELB *" \
        --query 'length(NetworkInterfaces)' --output text 2>/dev/null || echo 0)
      [ "$COUNT" = "0" ] && break
      sleep 5
    done
  fi

  # Auto-created k8s-elb-* security groups
  mapfile -t SG_IDS < <(aws ec2 describe-security-groups --region "$AWS_REGION" \
    --filters "Name=vpc-id,Values=${VPC_ID}" "Name=group-name,Values=k8s-elb-*" \
    --query 'SecurityGroups[].GroupId' --output text | tr '\t' '\n' | sed '/^$/d')
  for SG in "${SG_IDS[@]}"; do
    echo "[destroy-eks] deleting orphan SG: $SG"
    aws ec2 delete-security-group --region "$AWS_REGION" --group-id "$SG" || true
  done
fi

# ── 4. terraform destroy ─────────────────────────────────────────────────────
echo "[destroy-eks] terraform destroy in ${TF_DIR}"
terraform -chdir="$TF_DIR" destroy -auto-approve

echo "[destroy-eks] done"
