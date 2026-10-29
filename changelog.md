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

### Changed

- New projects use the `OPENAI_BACKEND` setting (default `openai`) instead of always `azure`
- S3, Azure OpenAI and Together.ai variables are optional; S3 is only needed for image uploads
- Dashboard (production profile) runs on port 8081 so it no longer clashes with the frontend

### Deprecated

### Fixed

- Switching a project's OpenAI backend in the dashboard had no effect
- Unsupported `model` values now show an error in the chat instead of failing silently

### Security

### Removed

## [1.0.0] - 2025-11-03

### Added

[unreleased]: https://github.com/center-for-humans-and-machines/simple-chat/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/center-for-humans-and-machines/simple-chat/releases/tag/v1.0.0
