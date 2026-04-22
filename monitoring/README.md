# Monitoring

**Prometheus + Grafana** on EKS via the `kube-prometheus-stack` Helm chart. The Jenkins EC2 is scraped as an extra target for host and Jenkins job metrics.

---

## 1. Install on EKS

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install kube-prom prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/kube-prom-values.yaml
```

Installs Prometheus, Alertmanager, Grafana, node-exporter (on every EKS worker), and kube-state-metrics — worker CPU/memory/disk/network, Kubernetes objects, and pod metrics are collected automatically.

---

## 2. Open Grafana

```bash
kubectl -n monitoring port-forward svc/kube-prom-grafana 3000:80
# http://localhost:3000   user: admin   pass: admin  (change it)
```

Prometheus UI (optional):

```bash
kubectl -n monitoring port-forward svc/kube-prom-kube-prometheus-prom-prometheus 9090
```

---

## 3. Scrape Jenkins EC2

Two targets outside the cluster (network reach required from EKS worker subnets):

| Target               | URL                                    |
| -------------------- | -------------------------------------- |
| Jenkins app metrics  | `http://<JENKINS_EIP>:8080/prometheus` |
| Host metrics (node)  | `http://<JENKINS_EIP>:9100/metrics`    |

Wire it up:

1. `terraform -chdir=terraform/jenkins-master apply` — opens TCP `9100` in the Jenkins SG.
2. Run the Ansible playbook — installs the Jenkins Prometheus plugin and runs `node_exporter` as a Docker container on the host.
3. Replace `<JENKINS_EIP>` in [`kube-prom-values.yaml`](kube-prom-values.yaml) with `terraform -chdir=terraform/jenkins-master output -raw instance_public_ip`.
4. Re-run the `helm upgrade` above.

For production, restrict `9100` to your CIDR or the EKS NAT gateway IP instead of `0.0.0.0/0`.

---

## 4. Grafana dashboards

Import by ID (Grafana → Dashboards → New → Import):

| ID             | Dashboard                                                   |
| -------------- | ----------------------------------------------------------- |
| **1860**       | Node Exporter Full (Jenkins host + cluster nodes)           |
| **9964**       | Jenkins (Prometheus plugin) — CPU, memory, jobs, queue      |
| **315**        | Kubernetes cluster monitoring (overall EKS view)            |
| **747 / 6417** | Kubernetes / Pod resource usage                             |

---

## Cleanup

```bash
helm uninstall kube-prom -n monitoring
kubectl delete ns monitoring
```
