# Jenkins CI/CD

This folder holds **Declarative Pipeline** definitions used by Jenkins jobs in this repo. The Jenkins controller is deployed on AWS EC2 (Docker); provisioning and plugins are applied with Ansible—see below.

## Pipelines

| File | Typical Jenkins job name | Purpose |
|------|-------------------------|---------|
| [`Jenkinsfile.cli`](Jenkinsfile.cli) | `cli-ci` | CLI image: build, test, push to ECR/Docker Hub; optional **Tag Release** on `main` using GitHub credentials from AWS Secrets Manager. |
| [`Jenkinsfile.engine`](Jenkinsfile.engine) | `engine-ci` | Engine image: build, test, push to ECR. |
| [`Jenkinsfile.cd`](Jenkinsfile.cd) | `cd` | Deploy to EKS: kustomize overlay, apply manifests, rollout **StatefulSet** `sawe-engine` and **Deployment** `sawe-cli`. Triggers after successful `cli-ci` and `engine-ci`. |

- **CI** jobs use `githubPush()` where the plugin supports it; the Ansible playbook also configures SCM polling on `cli/` and `engine/` paths.
- **CD** uses the EC2 **instance profile** for AWS (no Jenkins “aws-credentials” credential). `kubectl` is installed into the workspace if missing.
- **Git tag push** (CLI) reads secret `RonGitUser` via `aws secretsmanager get-secret-value`. Ensure IAM on the Jenkins host allows that call.

## Repo layout (related)

| Path | Role |
|------|------|
| [`../ansible/playbooks/configure-jenkins.yml`](../ansible/playbooks/configure-jenkins.yml) | Installs Docker, runs Jenkins container (`jenkins/jenkins:lts-jdk21`), plugins, AWS CLI in container, and Groovy init for `cli-ci`, `engine-ci`, `cd` jobs. |
| [`../terraform/jenkins-master/`](../terraform/jenkins-master/) | Terraform for Jenkins EC2, security groups, IAM (including EKS/ECR permissions for CD). |
| [`../terraform/devops-eks-cluster/`](../terraform/devops-eks-cluster/) | EKS cluster; includes EKS access entry for the Jenkins EC2 role. |
| [`../configure-env/`](../configure-env/) | Local `.env` template: `JENKINS_EIP` for Ansible inventory, Docker Hub / GitHub values; [`export-env.sh`](../configure-env/export-env.sh) syncs credentials to Secrets Manager. |
| [`../k8s/`](../k8s/) | Kubernetes manifests applied by `Jenkinsfile.cd`. |

## Secrets and inventory

1. Copy [`configure-env/.env.example`](../configure-env/.env.example) to `configure-env/.env` and set `JENKINS_EIP`, registry tokens, and secret IDs.
2. Run `./configure-env/export-env.sh` (with AWS CLI credentials) to update Secrets Manager.
3. Ansible dynamic inventory [`../ansible/inventory.sh`](../ansible/inventory.sh) loads `configure-env/.env` for the Jenkins host IP.

## Local Docker (reference only)

For a quick local controller (not the same as the EC2/Ansible setup):

```bash
docker run -d -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  --name jenkins \
  jenkins/jenkins:lts-jdk21
```

The production-like image tag and extra packages inside the container match what the Ansible playbook installs (`python3`, Docker CLI inside Jenkins, AWS CLI, etc.). Data survives in the `jenkins_home` volume; image-only changes require rebuild or re-running the playbook.

## Dependencies inside the Jenkins container

The playbook installs tooling inside the running Jenkins container (Python, Docker CE, `awscli`, `jenkins` user in `docker` group). If you recreate the container without the playbook, those steps must be repeated—or bake them into a custom image.
