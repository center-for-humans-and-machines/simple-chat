# GitHub Actions Deployment Guide

**This guide was automatically generated, but manually reviewed.**

The documentation was inspired from our own workflows to deploy online experiments in our lab.

---

This document explains how to set up and use the GitHub Actions workflows for deploying Simple Chat.

## Overview

The GitHub Actions workflows:

- **Main workflow**: `.github/workflows/deployment.yml` - Builds and deploys all three services
- **Reusable action**: `.github/actions/deploy-helm/action.yml` - Common deployment logic

## Required Secrets

Configure these secrets in your GitHub repository settings:

### Docker Registry

- `DOCKER_USERNAME` - Username for Docker registry
- `DOCKER_PASSWORD` - Password/token for Docker registry

### Kubernetes Access

- `KUBECONFIG` - [Base64](https://en.wikipedia.org/wiki/Base64) encoded kubeconfig file for cluster access

### Application Secrets (Backend)

- `MONGO_URL` - MongoDB connection string
- `MONGO_OPLOG_URL` - MongoDB oplog URL
- `OPENAI_API_KEY` - OpenAI API key
- `OPENAI_BASE_URL` - OpenAI base URL
- `OPENAI_DEFAULT_MODEL` - Default OpenAI model
- `OPENAI_BACKEND` - OpenAI backend configuration
- `S3_ENDPOINT` - Object storage endpoint
- `S3_REGION_NAME` - Object storage region name
- `S3_ACCESS_KEY` - Object storage access key
- `S3_SECRET_KEY` - Object storage secret key
- `S3_BUCKET_NAME` - Object storage bucket name
- `TOGETHER_AI_URL` - Together AI URL
- `TOGETHER_AI_KEY` - Together AI API key
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `AZURE_OPENAI_BASE_URL` - Azure OpenAI base URL

## Required Variables

Configure these variables in your GitHub repository settings:

- `CLUSTER_BASE_URL` - Base URL for your cluster (default: `example.com`)
- `DOCKER_REGISTRY_PREFIX` - Docker registry prefix (default: `registry.example.com`)

## Workflow Triggers

### Automatic Deployment

- **Push to `main`**: Deploys to production environment
- **Push to `dev`**: Deploys to development environment
- **Pull requests**: Builds and tests without deployment

## Deployment Process

Each service follows this process:

1. **Environment Setup**: Calculate image names, URLs, and timestamps
2. **Build**: Install dependencies and build the application
3. **Docker**: Build and push Docker images (deployment branches only)
4. **Deploy**: Use Helm to deploy to Kubernetes (deployment branches only)

## Service URLs

After deployment, services are accessible at:

### Production (`main` branch)

- Backend: `https://simple-chat-backend.example.com`
- Frontend: `https://simple-chat-frontend.example.com`
- Dashboard: `https://simple-chat-dashboard.example.com`

### Development (`dev` branch)

- Backend: `https://simple-chat-backend-{branch}.example.com`
- Frontend: `https://simple-chat-frontend-{branch}.example.com`
- Dashboard: `https://simple-chat-dashboard-{branch}.example.com`

## Troubleshooting

### Common Issues

1. **Kubernetes Authentication**: Ensure the `kubeconfig` secret is properly [base64](https://en.wikipedia.org/wiki/Base64) encoded

   _**Note:** A file that is used to configure access to clusters is called a kubeconfig file. This is a generic way of referring to configuration files. It does not mean that there is a file named kubeconfig._
   Source: [Kubernetes Docs](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)

2. **Docker registry**: Verify `DOCKER_USERNAME` and `DOCKER_PASSWORD` are correct
3. **Missing secrets**: Check all required secrets are configured
4. **Helm deployment failures**: Review Kubernetes events and pod logs

### Debug Commands

```bash
# Check deployment status
kubectl get deployments -n simple-chat

# View pod logs
kubectl logs -n simple-chat deployment/simple-chat-backend-main

# Check ingress
kubectl get ingress -n simple-chat
```
