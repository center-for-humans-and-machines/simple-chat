# Kubernetes

This directory contains [Helm](https://helm.sh/) Charts to deploy Simple Chat on a [Kubernetes](https://kubernetes.io/) cluster.

## [CI/CD](https://www.atlassian.com/continuous-delivery/principles/continuous-integration-vs-delivery-vs-deployment)

We include a Proof-of-Concept [GitHub Actions](https://github.com/features/actions) setup to automate deployment to Kubernetes clusters. The exact setup is usually infrastructure-specific. The files in [`.github/workflows/`](../.github/workflows/) can be used as a starting point.

In a nutshell, the steps needed to deploy each service are:

1. Build the application using a Dockerfile. The output is a Docker image.
1. Push the Docker image to a container registry (e.g., Docker Hub, GitHub Container Registry).
1. Deploy the Docker image to a Kubernetes cluster using Helm charts. Expose the services using Ingress resources.

All services (backend, frontend, dashboard) reuse the same Helm Charts located in [charts/web-service/](../kubernetes/web-service/). A comprehensive guide is available in [github-actions.md](./github-actions.md).

### GitLab CI/CD Architecture

Similarly, in GitLab CI/CD, the deployment pipelines could be structured as follows (relative to root directory):

**Main Pipeline** (`.gitlab-ci.yml`)

- **Backend Pipeline** (`backend/.gitlab-ci.yml`)
- **Frontend Pipeline** (`frontend/.gitlab-ci.yml`)
- **Dashboard Pipeline** (`dashboard/.gitlab-ci.yml`)
