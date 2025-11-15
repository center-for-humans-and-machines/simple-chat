# Deployment

This step assumes that the frontend and backend `.env` files have already been created as described in the [readme](../readme.md#requirements). The backend `.env` file requires access to object storage for image uploads. Options for object storage include Amazon S3 and MinIO. The following guide uses terminology of [software engineering environments](https://dev.to/flippedcoding/difference-between-development-stage-and-production-d0p)—the different stages where code is built, tested, and deployed, such as development and production.

**First-time local installation tutorial:**

[![Watch the video](https://img.youtube.com/vi/M8G7-EQHCxc/hqdefault.jpg)](https://youtu.be/M8G7-EQHCxc)

## Docker Compose

Simple Chat includes a Docker Compose file for local development. The application can be started using the shell script with the same name and offers two profiles: development and production. The development profile supports hot reloading for the frontend and volume mounting, which are disabled in the production profile. Health checks on the modular components ensure transparent error logging.

## Scripts

[Docker Compose](../compose.yml) is used to run the application in development mode. The scripts below assume you are in the root directory of the project.

- Build application

  ```bash
  ./script/build
  ```

- Start application
  - in **development** environment:

    Frontend will be accessible on localhost:1234 and dashboard on localhost:3001

    ```bash
    ./script/start-dev
    ```

  - in **production** environment:

    It builds the react project and use nginx to serve it. Frontend will be accessible on localhost:8080

    ```bash
    ./script/start-prod
    ```

- Stop application
  - in **development** environment:

    ```bash
    ./script/stop-dev
    ```

  - in **production** environment:

    ```bash
    ./script/stop-prod
    ```

- Stop and remove application (local data in database will be lost)
  - in **development** environment:

    ```bash
    ./script/destroy-dev
    ```

  - in **production** environment:

    ```bash
    ./script/destroy-prod
    ```

## Production

Dockerfiles for [frontend](../frontend/Dockerfile) and [backend](../backend/Dockerfile) are used to build the application images for production.

The variable `REACT_APP_BACKEND_URL` in the production environment cannot be specified in the [compose.yml](../compose.yml) file because the production Docker image already contains the built frontend code. Instead, it should be set in the `.env` file of the frontend before building the Docker image.

## Kubernetes

Kubernetes manifests for Simple Chat are templated with Helm and stored in the [web-service](../kubernetes/web-service/) directory. Helm facilitates deployment by converting repetitive and environment-specific configurations into parameterized templates. Researchers can customize deployments by changing values in `values.yaml` like replica counts, resource limits or observability settings without modifying the underlying YAML. Helm then renders these templates into concrete Kubernetes resources and applies them consistently across clusters. This approach ensures reproducible deployments, simplifies upgrades through versioned releases and supports experiment-specific customization while maintaining a shared baseline configuration.

The Helm chart follows standard conventions, including a [`Chart.yaml`](../kubernetes/web-service/Chart.yaml) file for metadata, a [`values.yaml`](../kubernetes/web-service/values.yaml) file for default configurations, and resource templates in the [`templates/`](../kubernetes/web-service/templates/) directory such as [`deployment.yml`](../kubernetes/web-service/templates/deployment.yml), [`service.yml`](../kubernetes/web-service/templates/service.yml), and [`ingress.yml`](../kubernetes/web-service/templates/ingress.yml). For a first-time installation, users must create a namespace in the Kubernetes cluster and install the chart using a terminal command. The exact commands are available in our [Kubernetes readme](../kubernetes/readme.md). Through `values.yaml`, users can configure parameters like resource requests and limits, sticky sessions, and replica counts. Deployments can also be integrated with cloud providers, like Cloudflare, offering bot protection.

## Application and LLM Observability

The Helm chart ensures experimental robustness through two complementary observability layers:

- **[Sentry](./observability/sentry.md)** provides application-level monitoring: setting `sentry_enabled: true` and supplying a valid Data Source Name (DSN) in `sentry_dsn` activates automatic reporting of runtime exceptions, performance issues, and user-facing errors.

- **[Langfuse](./observability/langfuse.md)** adds LLM-level observability by tracing prompts, model responses, costs, latencies, and metadata such as participant IDs or experimental conditions. It thus enables fine-grained analysis of conversational behavior, error diagnosis, and reproducibility in LLM-driven experiments. Langfuse can be deployed either self-hosted or as a managed service, and it also supports version-controlled prompt management.

For detailed setup instructions, see the [observability documentation](./observability/).
