# Langfuse - LLM Observability

Langfuse provides LLM observability and tracing for Simple Chat. By default, Langfuse is disabled.

## Requirements

1. Create a free account at [cloud.langfuse.com](https://cloud.langfuse.com)
2. Create a new project in Langfuse
3. Copy your project's public and secret keys from Settings
4. Add to your `.env` file:

```bash
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, defaults to cloud
```

Langfuse initializes only when `LANGFUSE_ENABLED=true` and the keys are set.

## Usage

Once configured, Langfuse automatically traces all LLM calls using the `@observe` decorator.

## Configuration

### Backend

- [settings.py](../../backend/src/models/settings.py#L28-L39) - Configuration
- [llm_model.py](../../backend/src/utils/llm_model.py#L21-L36) - Conditional decorator setup
- [llm_model.py](../../backend/src/utils/llm_model.py#L94) - `@conditional_observe` on `call_model`

**Traces:** All LLM calls with inputs, outputs, timing, token usage, and metadata (session_id, participant_id, experiment_id, model)

### Best Practices

- Keep `LANGFUSE_ENABLED=false` in development or use a tag to maintain separate environments
- Monitor token usage to control costs
