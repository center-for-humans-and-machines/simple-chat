# Frontend

The frontend is written in TypeScript using [React](https://react.dev/) and bundled with [Parcel JS](https://parceljs.org). It provides the user interface for participants to interact with the chat system.

## Upload image

The `gpt-4o` model supports image, too. In the case you want to use `gpt-4o` without uploading image feature, use a URL below. `YOUR_SIMPLE_CHAT_FRONTEND_URL` is a placeholder for your actual Simple Chat frontend URL.

`https://YOUR_SIMPLE_CHAT_FRONTEND_URL/?pid=[project_id]&participant_id=[participant_id]&experiment_id=[experiment_id]&model=gpt-4o&upload_image=false`

### Hide camera button in chat interface

The GPT-4o and similar models support uploading images. To disable this feature, add `&upload_image=false` at the end of the URL when integrating it as an iframe.

## Hide chat input in chat interface

To disable the entire chat input form, add `&chat_input=false` at the end of the URL when integrating it as an iframe.

`https://YOUR_SIMPLE_CHAT_FRONTEND_URL/?pid=[project_id]&participant_id=[participant_id]&experiment_id=[experiment_id]&model=gpt-4o&chat_input=false&custom_system_message_id=[custom_system_message_id]`

This could be useful in combination with a custom system message that sets `assistant_first` to `true`, which makes the assistant start the conversation without waiting for user input. In this case, the participant will only see the assistant's message when loading the chat interface, and there will be no input box for the participant to type in. This setup is ideal for scenarios where the researcher wants to observe how participants react to the assistant's initial message without any influence from their own input.

Example custom system message creation with `assistant_first` set to `true`:

```bash
curl --request POST \
  --url http://YOUR_SIMPLE_CHAT_BACKEND_URL/project/custom_system_message \
  --header 'content-type: application/json' \
  --data '{
  "project_id": "YOUR_PROJECT_ID",
  "requested_by": "myemail@provider.com",
  "system_message": "You are a plant lover.",
  "assistant_first": "yes",
  "first_message": "What is your favorite plant?"
}'
```

The previous example uses `YOUR_PROJECT_ID` as a placeholder for the actual project ID, and `YOUR_SIMPLE_CHAT_BACKEND_URL` as a placeholder for the actual backend URL. The `custom_system_message_id` in the frontend URL should be replaced with the ID returned from this API call.

## Initiate a conversation

To initiate a conversation, three query parameters must be specified:

- `pid`: Project ID from project registration
- `experiment_id`: Defined by researcher
- `participant_id`: Defined by researcher (might be piped in from URL, e.g., a Prolific ID).

The LLM can be defined by `model=`, but it is optional.
The URL should be like this:
`https://YOUR_SIMPLE_CHAT_FRONTEND_URL/?pid=[xxx]&model=[xxx]&experiment_id=[xxx]&participant_id=[xxx]`

Placeholder, denoted as `[xxx]`, must be replaced with true values.
