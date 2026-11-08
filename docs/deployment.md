# Deployment

This step assumes that the frontend and backend `.env` files have already been created as described in the [readme](../readme.md#requirements). The backend `.env` file requires access to object storage for image uploads. Options for object storage include Amazon S3 and MinIO.

The following guide uses terminology of [software engineering environments](https://dev.to/flippedcoding/difference-between-development-stage-and-production-d0p)—the different stages where code is built, tested, and deployed, such as development and production.

**First-time local installation tutorial:**

[![Watch the video](https://img.youtube.com/vi/M8G7-EQHCxc/hqdefault.jpg)](https://youtu.be/M8G7-EQHCxc)

## Docker Compose

Simple Chat includes a Docker Compose file for local development. It offers two profiles: development and production. The development profile supports hot reloading for the frontend and volume mounting, which are disabled in the production profile. Health checks on the modular components ensure transparent error logging.

## Commands

[Docker Compose](../compose.yml) runs the application. Run the commands below from the root directory of the project.

| Action                                        | Development                                        | Production                                          |
| --------------------------------------------- | -------------------------------------------------- | --------------------------------------------------- |
| Build and start                               | `docker compose --profile dev up --build --detach` | `docker compose --profile prod up --build --detach` |
| Stop                                          | `docker compose --profile dev stop`                | `docker compose --profile prod stop`                |
| Stop and remove (local database data is lost) | `docker compose --profile dev down --volumes`      | `docker compose --profile prod down --volumes`      |

The development frontend is accessible on localhost:1234 and the dashboard on localhost:3001. The production profile builds the React projects and serves them with nginx; the frontend is accessible on localhost:8080 and the dashboard on localhost:8081.

## Production

Dockerfiles for [frontend](../frontend/Dockerfile) and [backend](../backend/Dockerfile) are used to build the application images for production.

The variable `REACT_APP_BACKEND_URL` in the production environment cannot be specified in the [compose.yml](../compose.yml) file because the production Docker image already contains the built frontend code.
Instead, it should be set in the `.env` file of the frontend before building the Docker image.

## Application and LLM Observability

Two optional observability layers help to keep experiments robust:

- **[Sentry](./observability/sentry.md)** provides application-level monitoring: setting `SENTRY_ENABLED=true` and supplying a valid Data Source Name (DSN) activates automatic reporting of runtime exceptions, performance issues, and user-facing errors.

- **[Langfuse](./observability/langfuse.md)** adds LLM-level observability by tracing prompts, model responses, costs, latencies, and metadata such as participant IDs or experimental conditions. It thus enables fine-grained analysis of conversational behavior, error diagnosis, and reproducibility in LLM-driven experiments.
  Langfuse can be deployed either self-hosted or as a managed service, and it also supports version-controlled prompt management.

For detailed setup instructions, see the [observability documentation](./observability/).
