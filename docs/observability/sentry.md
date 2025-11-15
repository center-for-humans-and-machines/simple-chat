# Sentry - Error Tracking

Sentry provides error tracking and performance monitoring for Simple Chat. By default, Sentry is disabled. Academic users can apply for [an education plan](https://sentry.io/for/education/).

## Requirements

1. Create a free account at [sentry.io](https://sentry.io)
2. Create two projects: one for [Python/FastAPI](https://docs.sentry.io/platforms/python/integrations/fastapi/) (backend) and one for [React](https://docs.sentry.io/platforms/javascript/guides/react/) (frontend)
3. Copy each project's [DSN](https://docs.sentry.io/concepts/key-terms/dsn-explainer/) (format: `https://key@o0.ingest.sentry.io/project`)
4. Add to your `.env` file:

```bash
SENTRY_ENABLED=true
SENTRY_DSN=https://YOUR@DSN.ingest.de.sentry.io/YOUR_SENTRY_PROJECT
```

Sentry initializes only when both `SENTRY_ENABLED=true` and `SENTRY_DSN` are set.

## Usage

Once configured, Sentry automatically captures unhandled exceptions and performance traces.

## Configuration

### Backend

- [main.py](../../backend/src/main.py#L21-L30) - Initialization
- [settings.py](../../backend/src/models/settings.py#L22-L27) - Configuration

**Captures:** Unhandled exceptions, performance traces (100%)

### Frontend

- [instrument.tsx](../../frontend/src/instrument.tsx) - Initialization
- [index.tsx](../../frontend/src/index.tsx) - Import

**Captures:** Errors, React component errors, performance traces (100%), navigation events, session replays (10% normal / 100% errors)

### Best Practices

- Keep `SENTRY_ENABLED=false` in development
- Use separate Sentry projects for frontend/backend
- Configure [data scrubbing](https://docs.sentry.io/platforms/python/data-management/sensitive-data/) to prevent PII leakage
- Adjust sampling rates for production traffic
