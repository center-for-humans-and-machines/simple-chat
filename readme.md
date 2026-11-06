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

    All variables defined in [`settings.py`](./backend/src/models/settings.py) must be set in the `.env` file.
    `AZURE_OPENAI_BASE_URL` and `AZURE_OPENAI_API_KEY` can be left empty if not using Azure OpenAI.

  - Create `.env` file in the **frontend** directory by copying the [`env.example`](./frontend/env.example) file:

    ```bash
    cp frontend/env.example frontend/.env
    ```

    The default values can be used for local development.

## Installation

- Refer to the [deployment](./docs/deployment.md) documentation for first-time installation.
- Refer to the [contributing](./contributing.md) documentation to set up a development environment for modifying the code.

## Usage

Refer to the [documentation](./docs/readme.md) folder for usage instructions.

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
