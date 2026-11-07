<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Quick Start section in the readme (clone, `.env`, Docker Compose, dashboard, embed, export)
- Default model per project, chosen when creating a project in the dashboard
- Iframe embed code and test chat link on the dashboard project page
- `GET /project/models` endpoint listing supported models
- Optional per-project rate limit on conversation starts and messages, counted per participant ID or per IP address (`TRUST_X_FORWARDED_FOR` for deployments behind a proxy)
- Optional per-project list of origins allowed to embed the chat; the production frontend sends a matching `Content-Security-Policy: frame-ancestors` header when `BACKEND_INTERNAL_URL` is set
- `CORS_ALLOWED_ORIGINS` setting to restrict which origins may call the backend (default `*`)

### Changed

- New projects use the `OPENAI_BACKEND` setting instead of always `azure`. It defaults to `azure`, so existing deployments are unchanged; `env.example` sets it to `openai`
- S3, Azure OpenAI and Together.ai variables are optional; S3 is only needed for image uploads
- Dashboard (production profile) runs on port 8081 so it no longer clashes with the frontend
- Single `.env` file in the repository root (from `env.example`) replaces `backend/.env` and `frontend/.env`
- Production frontend and dashboard take their public URLs from `CHAT_URL` and `BACKEND_URL` at build time
- Readme documents Docker Compose commands for a local run and for a production run on a single server
- MongoDB port is only published on `127.0.0.1`

### Deprecated

### Fixed

- Frontend Sentry no longer initializes when `SENTRY_ENABLED=false`
- Switching a project's OpenAI backend in the dashboard had no effect
- Unsupported `model` values now show an error in the chat instead of failing silently

### Security

- Researchers log in to the dashboard with their e-mail and a password, set by the admin when creating their first project, instead of the project ID; accounts are stored in the new `Researcher` collection
- `POST /project/register` requires an admin login
- Usage and limits dashboard routes require a login token and are limited to the admin and the project owner

### Removed

- GitHub Actions workflows (deployment and super-linter)
- Kubernetes manifests and Helm chart
- Start, stop, build and destroy scripts in `script/`; use the Docker Compose commands in the readme

## [1.0.0] - 2025-11-03

### Added

[unreleased]: https://github.com/center-for-humans-and-machines/simple-chat/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/center-for-humans-and-machines/simple-chat/releases/tag/v1.0.0
