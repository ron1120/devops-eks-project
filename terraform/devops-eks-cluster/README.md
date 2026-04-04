# EKS Cluster - Terraform

Simple Terraform setup that provisions an EKS cluster with its own VPC and a monitoring stack (Prometheus + Grafana).

## Architecture

```
VPC (10.0.0.0/16)
├── Public Subnet 1 (10.0.1.0/24) - us-east-1a
├── Public Subnet 2 (10.0.2.0/24) - us-east-1b
├── Internet Gateway
├── Route Table (0.0.0.0/0 → IGW)
│
├── EKS Cluster (Kubernetes 1.30)
│   └── Managed Node Group (AL2023 x86_64)
│       ├── Instance Type: t3.medium
│       ├── Desired: 2 | Min: 1 | Max: 3
│       └── IAM Roles: EKSWorkerNodePolicy, EKS_CNI_Policy, ECR ReadOnly
│
└── Helm Charts
    └── kube-prometheus-stack (namespace: monitoring)
        ├── Prometheus
        └── Grafana
```

## Files

| File | Description |
|------|-------------|
| `main.tf` | Providers, VPC, IAM, EKS cluster, node group, Helm releases |
| `variables.tf` | All configurable variables with defaults |
| `outputs.tf` | Cluster endpoint, name, VPC ID, region, Grafana access command |

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.0
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with credentials
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed

## Usage

### Deploy

```bash
cd terraform
terraform init
terraform apply
```

> **Note:** The EKS cluster takes ~10-15 minutes to provision. The node group adds another ~3-5 minutes after that.

### Connect to the Cluster

```bash
aws eks update-kubeconfig \
  --region $(terraform output -raw aws_region) \
  --name $(terraform output -raw cluster_name)
```

### Verify Nodes

```bash
kubectl get nodes
```

### Access Grafana

```bash
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
```

Then open **http://localhost:3000** and log in:
- **User:** `admin`
- **Password:** `admin` (or the value you set for `grafana_admin_password`)

### Access Prometheus

```bash
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
```

Then open **http://localhost:9090**

## Variables

| Name | Description | Default |
|------|-------------|---------|
| `aws_region` | AWS region | `us-east-1` |
| `project_name` | Project name for resource tagging | `devops-eks-project` |
| `cluster_name` | Name of the EKS cluster | `devops-eks-cluster` |
| `vpc_cidr` | CIDR block for the VPC | `10.0.0.0/16` |
| `subnet_cidr_1` | CIDR for public subnet 1 | `10.0.1.0/24` |
| `subnet_cidr_2` | CIDR for public subnet 2 | `10.0.2.0/24` |
| `instance_type` | EC2 instance type for nodes | `t3.medium` |
| `desired_size` | Desired number of worker nodes | `2` |
| `max_size` | Max number of worker nodes | `3` |
| `min_size` | Min number of worker nodes | `1` |
| `grafana_admin_password` | Admin password for Grafana | `admin` |

## Outputs

| Name | Description |
|------|-------------|
| `cluster_endpoint` | EKS API server endpoint |
| `cluster_name` | Name of the EKS cluster |
| `vpc_id` | ID of the created VPC |
| `aws_region` | AWS region used |
| `grafana_access` | kubectl port-forward command for Grafana |

## Tear Down

```bash
terraform destroy
```
