# Simple Chat Documentation

Simple Chat consists of the following components:

- Database ([MongoDB](https://www.mongodb.com))
- [Frontend](../frontend)
- [Backend](../backend)
- Dashboard
- Object storage

## Object Storage

This is used to store participant-uploaded images from chats and is accessed from the backend. Object storage options include [AWS S3](https://aws.amazon.com/s3/) or [MinIO](https://min.io/). Configuration for the object storage is done in [helpers.py](../backend/src/utils/helpers.py).

## Supported LLMs

The availability of LLMs depends on the LLM provider of your choice. In principle, any LLM that can be accessed via an API can be integrated into Simple Chat.

## Integrating Into Online Experiments

The process of adding Simple Chat to online experiments, like Qualtrics or oTree, is straightforward. In a nutshell, you need to add an iframe that points to your [deployed](./deployment.md) Simple Chat frontend URL with the required query parameters.

### Qualtrics

Add a question that contains HTML and add an iframe that points to your [deployed](./deployment.md) url and specify the query parameters for the system message and model as shown below. In the following example, `YOUR_SIMPLE_CHAT_FRONTEND_URL` is a placeholder for your actual Simple Chat frontend URL.

`https://YOUR_SIMPLE_CHAT_FRONTEND_URL/?pid=project_id&model=gpt-4o` and your system message and model should be used. `project_id` must be replaced with the actual project ID you registered before. We also offer an example Qualtrics template linked from the [README](https://github.com/center-for-humans-and-machines/simple-chat/blob/main/readme.md) of this repo.

### oTree

See the [oTree example](https://github.com/center-for-humans-and-machines/simple-chat-otree-walter-2025).

## Admin Dashboard

The dashboard is built with [React](https://react.dev/). Every researcher can directly download conversations, edit system messages, and search in conversations in the admin dashboard.

To log into the dashboard, enter your email and project ID. The project ID should be one of the project IDs which is created by your email address before.
