# Deployment

Simple Chat runs with [Docker Compose](../compose.yml). All settings are read from a single `.env` file in the repository root, created from [`env.example`](../env.example). The commands for a local run and for a production run on a single server are in the [readme](../readme.md#quick-start-local).

**First-time local installation tutorial:**

[![Watch the video](https://img.youtube.com/vi/M8G7-EQHCxc/hqdefault.jpg)](https://youtu.be/M8G7-EQHCxc)

## Profiles

The Compose file offers two profiles. Both start the backend and a MongoDB database.

| Profile | Command                                             | Chat frontend           | Dashboard               | Use                           |
| ------- | --------------------------------------------------- | ----------------------- | ----------------------- | ----------------------------- |
| `dev`   | `docker compose --profile dev up --build`           | <http://localhost:1234> | <http://localhost:3001> | Local testing and development |
| `prod`  | `docker compose --profile prod up --build --detach` | port 8080               | port 8081               | Running a study on a server   |

The `dev` profile serves the frontend and dashboard with hot reloading from the mounted source code. The `prod` profile builds them once and serves the static files with nginx. The backend listens on port 8000 in both profiles. Health checks on the components make errors visible in `docker compose logs`.

## Production

The production frontend and dashboard are built into the Docker images, so the browser-facing URLs must be known at build time. Set `CHAT_URL` and `BACKEND_URL` in `.env` and rebuild with `--build` after changing them. Survey platforms are served over HTTPS and only embed HTTPS pages, so put a reverse proxy with TLS in front of ports 8080, 8081 and 8000, as shown in the [readme](../readme.md#production-single-server).

Image uploads by participants require object storage, such as Amazon S3 or MinIO, configured with the `S3_*` variables.

## Application and LLM Observability

Two optional observability layers help to keep experiments robust:

- **[Sentry](./observability/sentry.md)** provides application-level monitoring: setting `SENTRY_ENABLED=true` and supplying a valid Data Source Name (DSN) activates automatic reporting of runtime exceptions, performance issues, and user-facing errors.

- **[Langfuse](./observability/langfuse.md)** adds LLM-level observability by tracing prompts, model responses, costs, latencies, and metadata such as participant IDs or experimental conditions. It thus enables fine-grained analysis of conversational behavior, error diagnosis, and reproducibility in LLM-driven experiments. Langfuse can be deployed either self-hosted or as a managed service, and it also supports version-controlled prompt management.

For detailed setup instructions, see the [observability documentation](./observability/).
