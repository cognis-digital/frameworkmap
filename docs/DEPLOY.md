# Deploying frameworkmap

`frameworkmap` ships a container and is deployable to any cloud or orchestrator.

| Target | How |
|---|---|
| **Docker Compose** | `docker compose -f deploy/docker-compose.yml up -d` |
| **Kubernetes** | `kubectl apply -f deploy/k8s.yaml` |
| **Terraform** | `cd deploy/terraform && terraform init && terraform apply` |
| **AWS** | ECS Fargate / App Runner / Lambda (container image) from `ghcr.io/cognis-digital/frameworkmap` |
| **Azure** | Container Apps / ACI: `az containerapp create --image ghcr.io/cognis-digital/frameworkmap` |
| **GCP** | Cloud Run: `gcloud run deploy frameworkmap --image ghcr.io/cognis-digital/frameworkmap` |
| **Fly.io / Render / Railway** | point at the Dockerfile |

CI publishes the image to GHCR on tag push (`.github/workflows/docker-publish.yml`).
