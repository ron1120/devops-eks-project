# Ansible

Provisioning and configuration for **Jenkins** (remote EC2) and the **EKS cluster** (local `kubectl`/`helm`/`aws` against the API). Dynamic inventory driven by `configure-env/.env`.

---

## Layout

| Path                                                                      | Purpose                                                                                                                              |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| [`ansible.cfg`](ansible.cfg)                                              | Default inventory = [`inventory.sh`](inventory.sh).                                                                                  |
| [`inventory.sh`](inventory.sh)                                            | Dynamic JSON inventory; reads `JENKINS_EIP` from [`../configure-env/.env`](../configure-env/.env).                                   |
| [`inventory.ini`](inventory.ini)                                          | Static fallback (replace `{{ JENKINS_EIP }}` manually).                                                                              |
| [`playbooks/configure-jenkins.yml`](playbooks/configure-jenkins.yml)      | Installs Docker, runs `jenkins/jenkins:lts-jdk21`, plugins, AWS CLI in container, Groovy init for `cli-ci`, `engine-ci`, `cd` jobs. |
| [`playbooks/configure-eks.yml`](playbooks/configure-eks.yml)              | Refreshes kubeconfig, installs `kube-prometheus-stack` + `loki-stack`, applies `k8s/base` manifests, waits for rollouts. Runs on localhost. |

---

## Prerequisites

- **Ansible** on your laptop.
- **SSH** to the Jenkins host as `ubuntu` with the key referenced by `inventory.sh` (default `~/aws_pems/awsFE.pem`).
- **`configure-env/.env`** with `JENKINS_EIP` set.

---

## Run

From the `ansible/` directory (recommended):

```bash
cd ansible

# Provision / update Jenkins (remote EC2 via SSH)
ansible-playbook playbooks/configure-jenkins.yml

# Configure a freshly applied EKS cluster (runs locally against the EKS API)
ansible-playbook playbooks/configure-eks.yml
#   skip monitoring for a quick redeploy:  --skip-tags monitoring
#   redeploy only the app:                 --tags app
```

Explicit inventory (from anywhere):

```bash
ansible-playbook -i ansible/inventory.sh ansible/playbooks/configure-jenkins.yml
ansible-playbook -i ansible/inventory.sh ansible/playbooks/configure-eks.yml
```

Dry run:

```bash
ansible-playbook playbooks/configure-jenkins.yml --check
```

---

## Related

| Area                                         | Path                                                                               |
| -------------------------------------------- | ---------------------------------------------------------------------------------- |
| Jenkins EC2 + IAM                            | [`../terraform/jenkins-master/`](../terraform/jenkins-master/)                     |
| Sync Docker Hub / GitHub secrets to AWS       | [`../configure-env/export-env.sh`](../configure-env/export-env.sh)                 |
| Pipeline definitions used by the seeded jobs | [`../jenkins/`](../jenkins/)                                                       |
