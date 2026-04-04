output "cluster_endpoint" {
  value = aws_eks_cluster.eks.endpoint
}

output "cluster_name" {
  value = aws_eks_cluster.eks.name
}

output "vpc_id" {
  value = aws_vpc.eks_vpc.id
}

output "aws_region" {
  value = var.aws_region
}

output "grafana_access" {
  value = "kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring"
}
