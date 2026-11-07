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


def is_reasoning_model(model: str) -> bool:
    """OpenAI reasoning models (GPT-5 family, o-series) reject sampling parameters
    such as `temperature`. The `-chat` variants are not reasoning models."""
    name = model.lower()
    return name.startswith(("gpt-5", "o1", "o3", "o4")) and "chat" not in name
