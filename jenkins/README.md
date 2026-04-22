# Jenkins CI/CD

Declarative Pipelines consumed by the Jenkins controller (runs as a Docker container on EC2, provisioned by Ansible).

---

## Pipelines

| File                                       | Job name    | Purpose                                                                                                                           |
| ------------------------------------------ | ----------- | --------------------------------------------------------------------------------------------------------------------------------- |
| [`Jenkinsfile.cli`](Jenkinsfile.cli)       | `cli-ci`    | Build, test, push `sawe-cli` to **Docker Hub + AWS ECR**. Optional **Tag Release** on `main` using GitHub PAT from Secrets Manager. |
| [`Jenkinsfile.engine`](Jenkinsfile.engine) | `engine-ci` | Same flow for `sawe-engine`.                                                                                                      |
| [`Jenkinsfile.cd`](Jenkinsfile.cd)         | `cd`        | Deploy to EKS: kustomize overlay → `kubectl apply -k` → rollout `sawe-engine` (StatefulSet) and `sawe-cli` (Deployment).           |

- **CI** triggers on GitHub push (via webhook) with `git diff` change detection on `cli/`, `engine/`, `docker/`, `VERSION`.
- **CD** triggers downstream on `cli-ci` / `engine-ci` success on `main`.
- **AWS auth** uses the Jenkins EC2 **instance profile** — no Jenkins-managed AWS credentials.
- **GitHub PAT / Docker Hub / Slack** are read from **AWS Secrets Manager** at runtime.

---

## Related

| Path                                                                                     | Role                                                                                                      |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| [`../ansible/playbooks/configure-jenkins.yml`](../ansible/playbooks/configure-jenkins.yml) | Installs Docker, runs Jenkins container, plugins, AWS CLI, Groovy init for the three jobs.                |
| [`../terraform/jenkins-master/`](../terraform/jenkins-master/)                           | Jenkins EC2 + SG + IAM (ECR push + EKS access).                                                          |
| [`../terraform/devops-eks-cluster/`](../terraform/devops-eks-cluster/)                   | EKS cluster + EKS access entry for the Jenkins role.                                                      |
| [`../configure-env/`](../configure-env/)                                                 | `.env` + [`export-env.sh`](../configure-env/export-env.sh) (syncs Docker Hub / GitHub / Slack to Secrets). |
| [`../k8s/`](../k8s/)                                                                     | Kubernetes manifests applied by `cd`.                                                                     |

---

## Setup (first time)

1. Fill [`configure-env/.env`](../configure-env/.env.example): `JENKINS_EIP`, Docker Hub, GitHub PAT, Slack.
2. `./configure-env/export-env.sh` — pushes secrets to AWS Secrets Manager.
3. `ansible-playbook -i ansible/inventory.sh ansible/playbooks/configure-jenkins.yml` — provisions the Jenkins container and seeds the three jobs.

---

## Local Jenkins (reference only)

Quick local controller (not the same as the EC2/Ansible setup):

```bash
docker run -d -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  --name jenkins \
  jenkins/jenkins:lts-jdk21
```

The Ansible playbook installs additional tooling inside the container (Python, Docker CLI, `awscli`, `jenkins` user in `docker` group). Recreate without the playbook and those steps must be repeated — or bake them into a custom image.
