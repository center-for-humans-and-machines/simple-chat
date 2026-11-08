models = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-5.1",
        "gpt-5.1-2025-11-13",
        "gpt-5.5",
        "gpt-5.5-2026-04-23",
    ],
    "together_ai": [
        "together_ai-meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "together_ai-deepseek-ai/DeepSeek-R1",
        "together_ai-deepseek-ai/DeepSeek-V4.1-Flash",
    ],
}

# every model a project or chat URL may use
available_models = [model for provider_models in models.values() for model in provider_models]

# Estimated list prices in USD per 1M tokens, used for the dashboard cost estimate.
# Update these when provider pricing changes; models missing here are shown without cost.
model_prices = {
    "gpt-4o": {"prompt": 2.50, "completion": 10.00},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
    "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
    "gpt-4": {"prompt": 30.00, "completion": 60.00},
    "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
    "meta-llama/Llama-3.3-70B-Instruct-Turbo": {"prompt": 0.88, "completion": 0.88},
    "deepseek-ai/DeepSeek-R1": {"prompt": 3.00, "completion": 7.00},
}


def is_reasoning_model(model: str) -> bool:
    """Identify reasoning models that reject sampling parameters."""
    name = model.lower()
    return name.startswith(("gpt-5", "o1", "o3", "o4")) and "chat" not in name
