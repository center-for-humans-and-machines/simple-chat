# Simple Chat

Simple Chat is a user-friendly web interface that facilitates and optimizes the integration of LLMs into online experiments. Simple Chat offers three core benefits:

1. An **embeddable chat interface** that eliminates the need for custom API coding,
1. a consistent interface **across survey platforms**, and
1. streaming responses that maintain conversational flow and reduce participant dropout.

> [!TIP]
> Don't want to deploy Simple Chat yourself? Researchers can use the hosted [Simple Chat as a Service](#simple-chat-as-a-service) with their own LLM API key.

Below are diagrams illustrating the architecture and chat interface:

<details><summary>Architecture</summary>
<p>

<!-- markdownlint-disable MD033 -->
<div align="center">

### Architecture <!-- markdownlint-disable-line MD001 -->

<img src="./docs/images/architecture.png" alt="Architecture" style="width: 85%; max-width: 600px;">

</p>
</details>

<details><summary>Chat interface</summary>
<p>

### Chat interface

<img src="./docs/images/chat.png" alt="Chat" style="width: 90%; max-width: 400px;">
</div>
<!-- markdownlint-enable MD033 -->

</p>
</details>

## Simple Chat as a Service

Simple Chat comes in two flavors:

- **Self-hosted Simple Chat (this repository)** — the open-source, community-driven version. You deploy and operate it on your own infrastructure (Docker Compose or Kubernetes) and have full control over the code, data, and configuration.
- **Simple Chat as a Service** — a hosted version operated by the [Center for Humans and Machines](https://www.mpib-berlin.mpg.de/chm) at the Max Planck Institute for Human Development. Researchers use it through a web dashboard without deploying anything themselves.

The hosted service is built on Simple Chat but extends it with features needed to run it as a multi-user platform, such as user accounts with email verification, role-based project access (Superadmin, Level 2 and Level 1 researchers), and per-project model and API-key configuration. **The source code of the service version is not published for safety and security reasons**, since it runs as shared infrastructure handling multiple research groups' data and API keys. This repository remains the openly available, self-hostable version of Simple Chat.

### Using the service

1. Read the [Simple Chat as a Service documentation](https://simple-chat.chm.mpib-berlin.mpg.de/).
1. Register an account on the [dashboard](https://simple-chat-dashboard.chm.mpib-berlin.mpg.de/) and verify your email address via the activation link (valid for 48 hours).
1. Create a new project in the dashboard, or ask a Superadmin or a Level 2 researcher of an existing project to add you to it.
1. Enter **your own LLM API key** under _Project Settings → [API & Model Architecture](https://simple-chat.chm.mpib-berlin.mpg.de/docs/researcher-guide/projects/project-settings/api-and-model-architecture)_, and select the model (and, for providers such as Together.AI or Fireworks, the API endpoint). Supported providers include OpenAI, GWDG, Together.AI, and Fireworks. The key is stored hidden and usage is billed by your provider to your account, so use a key approved by your institution.
1. Configure the system message and chat settings, activate the project, and [embed the chat](https://simple-chat.chm.mpib-berlin.mpg.de/docs/integration-guide/overview) in your survey platform (e.g., [Qualtrics](https://simple-chat.chm.mpib-berlin.mpg.de/docs/integration-guide/qualtrics)).

### Which one should I use?

| | Self-host (this repository) | Use the service |
| --- | --- | --- |
| **Setup** | Deploy with Docker / Kubernetes, configure database, object storage, and secrets | Register on the dashboard, no deployment needed |
| **Technical skills required** | Server administration, Docker, basic DevOps | None beyond using a web dashboard |
| **LLM API key** | Configured in the backend `.env` file | Entered per project in the dashboard |
| **Data storage** | On your own infrastructure, under your control | On infrastructure operated by MPIB |
| **Maintenance and updates** | Your responsibility | Handled by the operators |
| **Customization** | Full access to the source code; modify and extend freely | Configuration through the dashboard only |
| **Best for** | Labs with IT support, strict data-residency requirements, or a need to change the code | Researchers who want to run LLM-based studies quickly without managing servers |

In short: **use the service** if you want to start collecting data quickly with your own API key and do not want to run servers. **Self-host this repository** if you need full control over the code and data, need to customize Simple Chat, or your institution requires data to stay on its own infrastructure.

The rest of this README describes the self-hosted version.

## Requirements

- Install [Docker](https://docs.docker.com/desktop/install/mac-install/) version `24.0.5, build ced0996` or newer
- Install [Docker Compose plugin](https://docs.docker.com/compose/install/linux/) version `v2.20.2-desktop.1` or newer
- Define secrets
  - Create `.env` file in the **backend** directory by copying the [`env.example`](./backend/env.example) file:

    ```bash
    cp backend/env.example backend/.env
    ```

    Variables are described in [`env.example`](./backend/env.example) and [`settings.py`](./backend/src/models/settings.py).
    Azure OpenAI, Together.ai and object storage (S3) variables can be left empty if not used; S3 is only needed for participant image uploads.

  - Create `.env` file in the **frontend** directory by copying the [`env.example`](./frontend/env.example) file:

    ```bash
    cp frontend/env.example frontend/.env
    ```

    The default values can be used for local development.

## Quick Start

Run Simple Chat locally and hold a first test conversation. You only need Docker and an OpenAI API key.

1. Clone the repository and create the `.env` files:

   ```bash
   git clone https://github.com/center-for-humans-and-machines/simple-chat.git
   cd simple-chat
   cp backend/env.example backend/.env
   cp frontend/env.example frontend/.env
   ```

1. In `backend/.env`, set `OPENAI_API_KEY`, `DASHBOARD_USERNAME_ADMIN` (an email address) and `DASHBOARD_PASSWORD_ADMIN`. All other variables are optional.

1. Start the development stack:

   ```bash
   docker compose --profile dev up --build
   ```

   The first build takes a few minutes. The chat frontend runs on <http://localhost:1234>, the dashboard on <http://localhost:3001> and the backend on <http://localhost:8000>.

1. Open the dashboard and log in with `DASHBOARD_USERNAME_ADMIN` as email and `DASHBOARD_PASSWORD_ADMIN` in the project ID field.

1. Click **Create a new project**, enter a project ID (e.g. `my_study`), choose a model, write a system message and click **Create the project**.

1. On the project page, click **Open test chat** to chat with the model, or **Copy iframe code** to embed the chat in your survey, for example:

   ```html
   <iframe src="http://localhost:1234/?pid=my_study&participant_id=PARTICIPANT_ID" width="100%" height="600" style="border:none;"></iframe>
   ```

   Replace `PARTICIPANT_ID` with your survey platform's participant variable. See [Integrating Into Online Experiments](./docs/readme.md#integrating-into-online-experiments) for the optional query parameters.

1. Back on the project page, click **Download Conversations as JSON** to export the data.

To make Simple Chat reachable by participants, deploy it to a server as described in the [deployment](./docs/deployment.md) documentation.

## Installation

- Refer to the [deployment](./docs/deployment.md) documentation for first-time installation.
- Refer to the [contributing](./contributing.md) documentation to set up a development environment for modifying the code.

## Usage

Refer to the [documentation](./docs/readme.md) folder for usage instructions.

## Participant Limits

Each project can limit how participants use the chat. Set the limits in the dashboard: open a project and click **Usage & limits**. They are stored on the project in MongoDB (`limits` field) and enforced by the backend. By default every limit is off, so new and existing projects behave as before.

| Limit                             | Default                             | Behavior                                                                                                                                                                                |
| --------------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Max conversations per participant | No limit                            | Conversations a `participant_id` has sent a message in. Rounds 2, 3, ... of a multi-round study do not count. Not applied without a `participant_id`; use the allowlist to require one. |
| Max turns per conversation        | No limit                            | Participant messages per conversation. Messages copied from earlier rounds do not count. The chat closes after the last allowed turn.                                                   |
| Token cap per conversation        | No limit                            | Prompt and completion tokens per conversation.                                                                                                                                          |
| Token cap per project             | No limit                            | Prompt and completion tokens across all conversations and `/llm` API calls of the project. Once it is reached, new conversations and API calls are rejected, and running chats end.     |
| Participant allowlist             | Empty (everyone may join)           | Participant IDs (e.g. Prolific IDs) allowed to start a conversation, one per line.                                                                                                      |
| Rate limit                        | No limit                            | Conversation starts and messages per window, see below.                                                                                                                                 |
| Rate limit window                 | 60 seconds                          | Length of the rate limit window, at most 86400 seconds (one day).                                                                                                                       |
| Rate limit counted per            | Participant ID                      | `Participant ID` counts per `participant_id`, falling back to the IP address when the URL has none. `IP address` counts per IP address.                                                 |
| Allowed embedding origins         | Empty (any site may embed the chat) | Origins allowed to show the chat in an iframe, e.g. `https://*.qualtrics.com`, see below.                                                                                               |

When a limit is reached, the participant sees a short message instead of an error, and the chat input closes. The message does not say which limit was reached. A rate-limited message is not sent: it goes back into the input field with a notice to wait. Token caps are enforced before each model call: the backend reserves the prompt and the longest reply that still fits under every cap that applies (at most 4096 tokens) and passes that as `max_tokens` to the model, so a reply cannot run past the cap and concurrent calls share the remaining budget instead of all passing at once. Chat token counts are estimates made with tiktoken, so they can differ slightly from the provider's count.

**Rate limits behind a proxy.** By default the backend uses the address of the connection as the participant's IP. Behind a reverse proxy or Kubernetes ingress this is the proxy's address, so set `TRUST_X_FORWARDED_FOR=true` in `backend/.env` to use the `X-Forwarded-For` header instead. Only enable it when a proxy sets this header, because participants can otherwise send their own.

**Restricting embedding.** With allowed embedding origins set, the production frontend sends a `Content-Security-Policy: frame-ancestors` header with these origins, so browsers refuse to show the chat in an iframe on any other site. The frontend container gets the policy from the backend at `BACKEND_INTERNAL_URL` (set to `http://backend:8000` in [`compose.yml`](./compose.yml); in Kubernetes, set it to the backend URL). Without `BACKEND_INTERNAL_URL` the header is not sent. In addition, the backend refuses to start a conversation when the chat reports being embedded on another origin, which also covers the development frontend. Opening the chat URL directly, outside an iframe, stays possible, for example for the dashboard's test chat.

**CORS.** `CORS_ALLOWED_ORIGINS` in `backend/.env` limits which origins may call the backend. The default `*` allows all. Set it to the chat frontend and dashboard origins, e.g. `CORS_ALLOWED_ORIGINS=https://chat.example.com,https://dashboard.example.com`. The survey's origin is not needed, because the chat inside the iframe calls the backend from the frontend's origin.

## Citation

If you use Simple Chat in your research, please cite as follows:

- BibTeX:

  ```
  @misc{schettino2025facilitatingintegrationllmsonline,
        title={Facilitating the Integration of LLMs Into Online Experiments With Simple Chat},
        author={R. Bermudez Schettino and A. Dasmeh and L. Brinkmann},
        year={2025},
        eprint={2511.19123},
        archivePrefix={arXiv},
        primaryClass={cs.HC},
        url={https://arxiv.org/abs/2511.19123},
  }
  ```

- APA:

  Bermudez Schettino, R., Dasmeh, A., & Brinkmann, L. (2025). _Facilitating the Integration of LLMs Into Online Experiments With Simple Chat_. arXiv. https://doi.org/10.48550/arXiv.2511.19123

## Related

- Qualtrics example - [Download](https://drive.google.com/file/d/1cPyH_bUEBzdn5NsDzJvVUe9QytTyvbj3/view?usp=sharing).

  This Qualtrics template is a modified version of [Costello's Qualtrics template](https://publish.obsidian.md/qualtrics-documentation/Documentation+for+Using+the+Human-AI+Interaction+Qualtrics+File/Human-AI+interaction+Qualtrics+template+documentation).

- oTree example - [simple-chat-otree-walter-2025](https://github.com/center-for-humans-and-machines/simple-chat-otree-walter-2025)
- Readme template - [minimal-readme](https://github.com/rodrigobdz/minimal-readme)
- Format for `script` directory - [Shell Style Guide](https://github.com/rodrigobdz/styleguide-sh)
- See `healthcheck` Docker Compose file - [docker-compose-healthchecks](https://github.com/rodrigobdz/docker-compose-healthchecks)

## License

[CC BY 4.0](license)
