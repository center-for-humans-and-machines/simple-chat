# Frontend

The frontend is written in TypeScript using [React](https://react.dev/) and bundled with [Parcel JS](https://parceljs.org). It provides the user interface for participants to interact with the chat system.

## Upload image

The `gpt-4o` model supports image, too. In the case you want to use `gpt-4o` without uploading image feature, use a URL below. `YOUR_SIMPLE_CHAT_FRONTEND_URL` is a placeholder for your actual Simple Chat frontend URL.

`https://YOUR_SIMPLE_CHAT_FRONTEND_URL/?pid=[project_id]&participant_id=[participant_id]&experiment_id=[experiment_id]&model=gpt-4o&upload_image=false`

### Hide camera button in chat interface

The GPT-4o and similar models support uploading images. To disable this feature, add `&upload_image=false` at the end of the URL when integrating it as an iframe.

## Initiate a conversation

To initiate a conversation, three query parameters must be specified:

- `pid`: Project ID from project registration
- `experiment_id`: Defined by researcher
- `participant_id`: Defined by researcher (might be piped in from URL, e.g., a Prolific ID).

The LLM can be defined by `model=`, but it is optional.
The URL should be like this:
`https://YOUR_SIMPLE_CHAT_FRONTEND_URL/?pid=[xxx]&model=[xxx]&experiment_id=[xxx]&participant_id=[xxx]`

Placeholder, denoted as `[xxx]`, must be replaced with true values.
