<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Researchers list for the admin on the dashboard projects page, with each researcher's projects and a password reset (`GET /dashboard/researchers`, `PUT /dashboard/researchers/{email}/password`)
- Quick Start section in the readme (clone, `.env`, Docker Compose, dashboard, embed, export)
- Default model per project, chosen when creating a project in the dashboard
- Iframe embed code and test chat link on the dashboard project page
- `GET /project/models` endpoint listing supported models
- Optional per-project rate limit on conversation starts and messages, counted per participant ID or per IP address (`TRUST_X_FORWARDED_FOR` for deployments behind a proxy)
- Optional per-project list of origins allowed to embed the chat; the production frontend sends a matching `Content-Security-Policy: frame-ancestors` header when `BACKEND_INTERNAL_URL` is set
- `CORS_ALLOWED_ORIGINS` setting to restrict which origins may call the backend (default `*`)

### Changed

- New projects use the `OPENAI_BACKEND` setting instead of always `azure`. It defaults to `azure`, so existing deployments are unchanged; `.env.example` sets it to `openai`
- S3, Azure OpenAI and Together.ai variables are optional; S3 is only needed for image uploads
- Dashboard (production profile) runs on port 8081 so it no longer clashes with the frontend

### Deprecated

### Fixed

- Researcher emails are stored in lowercase and matched ignoring case, so `Alice@x.org` and `alice@x.org` are the same account
- Round 2, 3, ... started without the previous round's history when the chat URL had no `experiment_id` (or no `participant_id`)
- Frontend Sentry no longer initializes when `SENTRY_ENABLED=false`
- Switching a project's OpenAI backend in the dashboard had no effect
- Unsupported `model` values now show an error in the chat instead of failing silently

### Security

- Researchers log in to the dashboard with their e-mail and a password, set by the admin when creating their first project, instead of the project ID; accounts are stored in the new `Researcher` collection
- `GET /download/conversation/{session_id}` and `GET /download/conversation/messages/json/{session_id}` require a dashboard login and only allow the admin or the project owner
- Dashboard login tokens are signed with the new `DASHBOARD_TOKEN_SECRET` instead of `DASHBOARD_PASSWORD_ADMIN`, so a researcher's token cannot be used to guess the admin password offline
- `POST /project/register` requires an admin login
- All project dashboard routes (projects, conversations, settings, usage and limits) require a login token and are limited to the admin and the project owner

### Removed

- Kubernetes manifests, Helm chart and the `script/` wrappers for Docker Compose; the disabled GitHub Actions deployment workflow stays as a reference

## [1.0.0] - 2025-11-03

### Added

[unreleased]: https://github.com/center-for-humans-and-machines/simple-chat/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/center-for-humans-and-machines/simple-chat/releases/tag/v1.0.0
