# Jenkins Container Setup

## Base Image
```
jenkins/jenkins:lts
```

## Run Command
```bash
docker run -d -p 8080:8080 -p 50000:50000 -v jenkins_home:/var/jenkins_home --name jenkins jenkins/jenkins:lts
```

## Injected Dependencies

The following packages were manually installed inside the Jenkins container as `root`:

### Python
```bash
docker exec -u root jenkins bash -c "apt-get update && apt-get install -y python3 python3-venv python3-pip"
```
- `python3` (v3.13.5)
- `python3-venv`
- `python3-pip`

### Docker Prerequisites
```bash
docker exec -u root jenkins bash -c "apt-get install -y apt-transport-https ca-certificates gnupg lsb-release curl"
```
- `apt-transport-https`
- `ca-certificates`
- `gnupg`
- `lsb-release`
- `curl`

### Docker CE
```bash
docker exec -u root jenkins bash -c "curl -fsSL https://get.docker.com -o /tmp/get-docker.sh && sh /tmp/get-docker.sh"
```
- `docker-ce` (v29.3.1)
- `docker-ce-cli`
- `containerd.io`
- `docker-compose-plugin`
- `docker-buildx-plugin`

### Post-Install: Add Jenkins User to Docker Group
```bash
docker exec -u root jenkins bash -c "usermod -aG docker jenkins"
docker restart jenkins
```

> **Note:** These dependencies are lost if the container is recreated. Only data in the `jenkins_home` volume persists. To avoid reinstalling manually each time, consider building a custom Jenkins Docker image with these dependencies baked in.


### DEPENDENCIES NOTE:
On Setup Environment Stage pipeline is only used to handle other containers dependencies not jenkins, to use jenkins in cloud for CI/CD there is an ansible playbook used to install all jenkins dependencies.