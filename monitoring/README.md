# Observability

Full observability stack for the `devops-eks-cluster`:

| Concern     | Tool                                                        |
| ----------- | ----------------------------------------------------------- |
| Metrics     | Prometheus (via `kube-prometheus-stack`)                    |
| Dashboards  | Grafana (via `kube-prometheus-stack`, LoadBalancer Service) |
| Alerting    | Alertmanager → Slack (default + critical routes)            |
| Logging     | Loki + Promtail (`loki-stack`)                              |

Values files in this folder:

- [`kube-prom-values.yaml`](kube-prom-values.yaml) — Prometheus / Alertmanager / Grafana / node-exporter / kube-state-metrics.
- [`loki-values.yaml`](loki-values.yaml) — Loki log store + Promtail node agent.

---

## 1. Install metrics + dashboards + alerting

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install kube-prom prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/kube-prom-values.yaml
```

Installs Prometheus (20Gi gp2), Alertmanager (2Gi gp2), Grafana (5Gi gp2 + `LoadBalancer`), node-exporter on every worker, and kube-state-metrics. ~30 default `PrometheusRule` alerts ship with the chart (node down, pod crashloop, disk pressure, control-plane health, …).

## 2. Install logging

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm upgrade --install loki grafana/loki-stack \
  -n monitoring --create-namespace \
  -f monitoring/loki-values.yaml
```

Promtail runs as a DaemonSet and streams `/var/log/pods` into Loki. 7-day retention, 10Gi gp2 PVC.

---

## 3. Open Grafana

The chart exposes Grafana on an AWS ELB. Get the URL:

```bash
kubectl -n monitoring get svc kube-prom-grafana \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'; echo

kubectl -n monitoring get secret kube-prom-grafana \
  -o jsonpath='{.data.admin-password}' | base64 -d; echo   # default: admin
```

Prefer to keep it private? Use port-forward instead:

```bash
kubectl -n monitoring port-forward svc/kube-prom-grafana 3000:80
# http://localhost:3000   user: admin   pass: admin  (change it)
```

### Add Loki as a Grafana data source

Grafana UI → **Connections → Data sources → Add data source → Loki** → URL `http://loki:3100` → **Save & test**. Then **Explore → (Loki) → `{namespace="sawe"}`** to tail pod logs.

---

## 4. Dashboards

About 30 Kubernetes dashboards load automatically (Dashboards → Browse). Nice extras to import (Dashboards → New → Import by ID):

| ID        | Dashboard                                   |
| --------- | ------------------------------------------- |
| **1860**  | Node Exporter Full                          |
| **315**   | Kubernetes cluster monitoring (overall)     |
| **15757** | Kubernetes Views / Global                   |
| **13639** | Logs / App (Loki)                           |

---

## 5. Alerting → Slack

`alertmanager.config` in [`kube-prom-values.yaml`](kube-prom-values.yaml) routes:

- anything → `#alerts`
- `severity="critical"` → `#alerts-critical`

**Before the first `helm upgrade`**, replace the two `REPLACE/ME/WITH-YOUR-WEBHOOK` placeholders with an actual Slack Incoming Webhook URL (Slack → Apps → *Incoming Webhooks*). For a quick demo without Slack, point `api_url` at a free endpoint from [webhook.site](https://webhook.site).

Verify alert routing:

```bash
kubectl -n monitoring port-forward svc/kube-prom-kube-prometheus-alertmanager 9093:9093
# http://localhost:9093/#/status   → should show your receivers
```

Force a test alert (fires once, resolves in ~5m):

```bash
kubectl -n monitoring run alert-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -XPOST http://kube-prom-kube-prometheus-alertmanager:9093/api/v2/alerts \
    -H "Content-Type: application/json" \
    -d '[{"labels":{"alertname":"TestAlert","severity":"critical"}}]'
```

---

## 6. Prometheus UI (scrape targets, rules, ad-hoc PromQL)

```bash
kubectl -n monitoring port-forward svc/kube-prom-kube-prometheus-prometheus 9090:9090
# http://localhost:9090/targets   — every target should be UP
# http://localhost:9090/rules     — default recording & alerting rules
```

---

## Cleanup

```bash
helm uninstall loki       -n monitoring
helm uninstall kube-prom  -n monitoring
kubectl delete ns monitoring
```

> The Grafana LoadBalancer Service creates a ~$18/mo Classic ELB. Uninstalling the chart removes it. `terraform destroy` on `devops-eks-cluster` will also tear down the whole cluster including this stack.
