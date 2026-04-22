# CI/CD architecture — `devops-eks-project`

A minimal, presentation-ready view of **Git → Jenkins → AWS (ECR + EKS)**.

---

## One-slide diagram

```mermaid
flowchart LR
  DEV[Developer\ngit push]
  GH[GitHub]
  CI[Jenkins CI\ncli-ci, engine-ci]
  ECR[(AWS ECR)]
  CD[Jenkins CD\ncd]
  EKS[(AWS EKS)]
  MON[Prometheus + Grafana]

  DEV --> GH --> CI --> ECR
  CI --> CD --> EKS
  ECR -.->|pull| EKS
  EKS --> MON
```

---

## What each block does

| Block | Does | In the repo |
|-------|------|-------------|
| **Jenkins CI** | Test, build, push images | `jenkins/Jenkinsfile.cli`, `jenkins/Jenkinsfile.engine` |
| **ECR** | Private image registry for `sawe-cli`, `sawe-engine` | AWS account / region `us-east-1` |
| **Jenkins CD** | Check ECR vs cluster, `kubectl apply -k`, rollout | `jenkins/Jenkinsfile.cd` + `k8s/` |
| **EKS** | Runs `sawe-cli` (Deployment) and `sawe-engine` (StatefulSet) | `terraform/devops-eks-cluster/`, `k8s/base/` |
| **Monitoring** | Prometheus + Grafana (Helm) in-cluster | `monitoring/`, `terraform/devops-eks-cluster/` |

---

## Provisioning (run once / on changes)

```mermaid
flowchart LR
  TF[Terraform\njenkins-master + eks-cluster]
  AN[Ansible\nconfigure-jenkins.yml]
  SM[(Secrets Manager)]

  TF --> EC2[Jenkins EC2]
  AN --> EC2
  TF --> EKS[(EKS)]
  SM -.-> EC2
```

- **Terraform**: EKS cluster, Jenkins EC2, IAM (EKS access entry + ECR for Jenkins).
- **Ansible**: installs Jenkins, Docker, AWS CLI, plugins, seeds jobs.
- **Secrets Manager**: Docker Hub + GitHub PAT, read by Jenkins via IAM (no Jenkins credentials UI).

Export `configure-env/.env` values with `configure-env/export-env.sh`.
