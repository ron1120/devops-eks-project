# Ansible

Provisioning and configuration for the **Jenkins controller** on AWS EC2 (Docker-based). There is one playbook today; inventory is generated from your local environment file.

## Layout

| Path | Purpose |
|------|---------|
| [`ansible.cfg`](ansible.cfg) | Uses [`inventory.sh`](inventory.sh) as the default inventory. |
| [`inventory.sh`](inventory.sh) | JSON dynamic inventory: reads **`JENKINS_EIP`** from [`../configure-env/.env`](../configure-env/.env). |
| [`inventory.ini`](inventory.ini) | Static template (placeholder host). Use only if you replace `{{ JENKINS_EIP }}` manually; normal runs use `inventory.sh`. |
| [`playbooks/configure-jenkins.yml`](playbooks/configure-jenkins.yml) | Installs Docker, runs the Jenkins container (`jenkins/jenkins:lts-jdk21`), plugins, AWS CLI in the container, and Groovy init scripts for `cli-ci`, `engine-ci`, and `cd` jobs. |

## Prerequisites

- **Ansible** on your machine (control node).
- **SSH access** to the Jenkins host as `ubuntu`, using the key path set in [`inventory.sh`](inventory.sh) (`~/aws_pems/awsFE.pem` by default — adjust there if your key lives elsewhere).
- **[`configure-env/.env`](../configure-env/README.md)** with `JENKINS_EIP` set to the instance Elastic IP (same value you use in AWS / Terraform).

## Run

From this directory:

```bash
cd ansible
ansible-playbook playbooks/configure-jenkins.yml
```

Override inventory or limit hosts if needed:

```bash
ansible-playbook -i inventory.sh playbooks/configure-jenkins.yml
```

Dry run (no changes):

```bash
ansible-playbook playbooks/configure-jenkins.yml --check
```

## Related

- **EC2 / IAM for Jenkins:** [`../terraform/jenkins-master/`](../terraform/jenkins-master/)
- **Secrets pushed to AWS (Docker Hub / GitHub for pipelines):** [`../configure-env/export-env.sh`](../configure-env/export-env.sh)
- **Pipeline definitions:** [`../jenkins/`](../jenkins/)
