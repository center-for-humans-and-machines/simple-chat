<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

- The backend uses Beanie 2 and PyMongo's async client, up from Beanie 1.30
  with Motor (SIM-XX)
- The backend runs on Pydantic 2 and FastAPI 0.162, up from Pydantic 1.10
  and FastAPI 0.95; settings now come from `pydantic-settings` (SIM-79)

### Deprecated

### Fixed

### Security

### Removed

- Kubernetes manifests, Helm chart and the `script/` wrappers for Docker Compose

## [1.0.0] - 2025-11-03

### Added

[unreleased]: https://github.com/center-for-humans-and-machines/simple-chat/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/center-for-humans-and-machines/simple-chat/releases/tag/v1.0.0
