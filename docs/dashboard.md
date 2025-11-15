# Dashboard

The dashboard is built with [React](https://react.dev/) and [Material-UI](https://mui.com/). It provides a web interface for researchers to manage projects, view conversations, and download chat data.

## Login

### Admin

Define the credentials `DASHBOARD_PASSWORD_ADMIN` and `DASHBOARD_USERNAME_ADMIN` in the `.env` file to login to dashboard and create projects.
Note: `DASHBOARD_USERNAME_ADMIN` in `.env` must be an email including `@`.

### User

To access the dashboard, navigate to the dashboard URL and sign in with:

- Email address (must match the `requested_by` email from project registration)
- Project ID (registered via the backend API)

The login authenticates against the backend at `/dashboard/login/{email}/{project_id}`.

## Project Management

After logging in, you can view all projects associated with your email address. For each project, you can:

- View project details (creation date, status, OpenAI backend)
- Toggle project status between active and deactive
- Switch between OpenAI backends (OpenAI or Azure)
- Edit the system message
- Edit the loading message shown to participants
- Download all conversations as JSON

## Viewing Conversations

Navigate to a project to see a list of all conversations. You can:

- Search conversations by model, participant ID, experiment ID, or conversation ID
- Download filtered conversations as JSON
- Click on any conversation to view its full details
- Download individual conversation data as JSON

Each conversation displays the complete chat history and metadata in JSON format.

## Environment Variables

Set the backend URL via the `REACT_APP_BACKEND_URL` environment variable. If not set, it defaults to `http://localhost:8000`.

## Updating the Logo

The images used in the dashboard can be found in the [`dashboard/public`](https://github.com/center-for-humans-and-machines/simple-chat/tree/main/dashboard/public) directory. The favicon is `favicon.ico` and it should have dimensions of 48x48 pixels. Other images can have a different aspect ratio. Replace these files with your own images to customize the dashboard appearance.
