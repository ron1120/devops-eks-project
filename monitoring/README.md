# Monitoring (Prometheus + Grafana)

Standard cluster monitoring using the `kube-prometheus-stack` Helm chart, plus the Jenkins EC2 scraped from Prometheus.

## 1) Install on EKS

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install kube-prom prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/kube-prom-values.yaml
```

This installs **Prometheus**, **Alertmanager**, **Grafana**, **node-exporter** (on every EKS worker), and **kube-state-metrics** — so worker CPU/memory/disk/network, Kubernetes objects, and pod metrics are collected automatically.

## 2) Open Grafana

Port-forward on your laptop:

```bash
kubectl -n monitoring port-forward svc/kube-prom-grafana 3000:80
# http://localhost:3000   user: admin   pass: admin  (change it)
```

Prometheus UI (optional):

```bash
kubectl -n monitoring port-forward svc/kube-prom-kube-prometheus-prom-prometheus 9090
```

## 3) Jenkins EC2 (outside the cluster)

Two targets are scraped from Prometheus and need **network reach** from the EKS worker subnets to the Jenkins host:

- **Jenkins app metrics** via the official **Prometheus** Jenkins plugin → `http://<JENKINS_EIP>:8080/prometheus`
- **Host metrics** via **node_exporter** → `http://<JENKINS_EIP>:9100/metrics`

The Ansible playbook [`ansible/playbooks/configure-jenkins.yml`](../ansible/playbooks/configure-jenkins.yml) installs the Jenkins Prometheus plugin and runs `node_exporter` as a Docker container on the Jenkins EC2. [`terraform/jenkins-master/main.tf`](../terraform/jenkins-master/main.tf) opens TCP `9100` in the Jenkins security group.

### Wire Prometheus to the Jenkins EC2

1. Apply Terraform so the Jenkins SG has port `9100` open (Prometheus scrape).
2. Run the Ansible playbook so the Jenkins container gets the Prometheus plugin and `node_exporter` runs on the host.
3. Replace `<JENKINS_EIP>` in [`kube-prom-values.yaml`](kube-prom-values.yaml) with the output of
   `terraform -chdir=terraform/jenkins-master output -raw instance_public_ip`.
4. Re-run the Helm upgrade above.
5. For a stricter setup: instead of opening `0.0.0.0/0` on `9100`, limit to your office CIDR or the public IP of an EKS NAT gateway.

### Grafana dashboards

Import these by ID (Grafana → Dashboards → New → Import):

- **1860** – Node Exporter Full (Jenkins host + any other node_exporter target)
- **9964** – Jenkins (official Prometheus plugin) — CPU, memory, job metrics, queue length
- **315** – Kubernetes cluster monitoring (Prometheus) — overall EKS view
- **747** / **6417** – Kubernetes / Pod resource usage

## Cleanup

```bash
helm uninstall kube-prom -n monitoring
kubectl delete ns monitoring
```
