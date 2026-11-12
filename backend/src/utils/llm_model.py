from typing import List, Optional

import math

import requests
import tiktoken
# Note: The openai-python library support for Azure OpenAI is in preview.
from openai import AsyncAzureOpenAI, AsyncOpenAI
from src.models.message import OpenAIMessage
from src.models.models import Project
from src.models.settings import get_settings
from src.utils.configs import is_reasoning_model, models
from src.utils.db import create_message
from src.utils.limits import limit_message, release_tokens, reserve_tokens
from src.utils.logging import setup_logger
from src.utils.usage import record_usage
from tenacity import retry, stop_after_attempt, wait_random_exponential

logger = setup_logger(__name__)

encoding = tiktoken.get_encoding("cl100k_base")


settings = get_settings()

# Conditional Langfuse integration
if settings.langfuse_enabled:
    from langfuse import get_client, observe

    def conditional_observe(func):
        """Apply @observe decorator when Langfuse is enabled"""
        return observe(func)

    # Initialize Langfuse client for flushing
    langfuse_client = get_client()
else:
    # Identity decorator that does nothing when Langfuse is disabled
    def conditional_observe(func):
        return func

    langfuse_client = None


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(5))
async def completion_with_backoff(client, **kwargs):
    # logger.info("here in completion_with_backoff")
    # return await client.chat.completions.create(**kwargs)
    if is_reasoning_model(kwargs["model"]):
        # Reasoning models reject `temperature`; they only use their default sampling.
        kwargs.pop("temperature", None)
        if settings.openai_reasoning_effort:
            # Sent as extra_body because the pinned openai SDK predates this parameter.
            kwargs["extra_body"] = {
                **kwargs.get("extra_body", {}),
                "reasoning_effort": settings.openai_reasoning_effort,
            }
    if (
        f"together_ai-{kwargs['model']}" in models["together_ai"]
        and settings.together_ai_reasoning_effort
    ):
        # Hybrid open-weights models (e.g. DeepSeek-V4.1-Flash) think by default;
        # "none" switches thinking off.
        kwargs["extra_body"] = {
            **kwargs.get("extra_body", {}),
            "reasoning_effort": settings.together_ai_reasoning_effort,
        }
    # On Azure the request names a deployment, which may differ from the model name.
    deployments = getattr(client, "azure_deployments", None)
    if deployments:
        kwargs["model"] = deployments.get(kwargs["model"], kwargs["model"])
    try:
        return await client.chat.completions.create(**kwargs)

    except Exception as e:
        logger.error("Error occurred in completion_with_backoff: %s", str(e))
        raise  # Re-raise exception after logging it


def init_model_endpoint(
    model: str, openai_backend: str
) -> AsyncOpenAI | AsyncAzureOpenAI:
    """
    Initialize the model endpoint based on the provided model name.

    This function sets up a global client to interact with OpenAI (including Azure OpenAI)
    based on the specified model. The client is initialized differently depending on the model's source:

    - If the model is found in the "openai" list, it checks the base URL to determine if Azure OpenAI should be used.
    - If the base URL contains the substring "azure", it initializes an `AsyncAzureOpenAI` client.
    - Otherwise, it defaults to an `AsyncOpenAI` client.

    Args:
        model (str): The name of the model to initialize.

    Raises:
        KeyError: If the model is not found in "openai" model lists.

    Returns:
        AsyncOpenAI | AsyncAzureOpenAI: The initialized client for the specified model.
    """

    # Guard clause: Initialize client if the model is in the OpenAI list and check for Azure usage
    if model in models["openai"]:
        logger.debug(f"Model {model} found in OpenAI models... Loading endpoint.")

        # Check if the OpenAI base URL contains "azure"
        if openai_backend.lower() == "azure":
            logger.debug(
                "Azure-specific base URL detected... Using AsyncAzureOpenAI client."
            )
            if settings.azure_openai_api_version == "v1":
                # Version-less v1 API, which Azure recommends for GPT-5 models.
                client = AsyncOpenAI(
                    api_key=settings.azure_openai_api_key,
                    base_url=settings.azure_openai_base_url.rstrip("/") + "/openai/v1/",
                )
            else:
                client = AsyncAzureOpenAI(
                    api_key=settings.azure_openai_api_key,
                    azure_endpoint=settings.azure_openai_base_url,
                    api_version=settings.azure_openai_api_version,
                )
            # Map model names to deployment names (AZURE_OPENAI_DEPLOYMENTS).
            client.azure_deployments = settings.azure_openai_deployments
        elif openai_backend.lower() == "openai":
            logger.debug(
                "Standard OpenAI base URL detected... Using AsyncOpenAI client."
            )
            client = AsyncOpenAI(api_key=settings.openai_api_key)
        return client

    if model in models["together_ai"]:
        # Use the async client so a Together AI response does not block the
        # event loop (and with it every other open chat) while it streams.
        client = AsyncOpenAI(
            api_key=settings.together_ai_key, base_url=settings.together_ai_url
        )
        return client

    # If the model is not recognized, raise an error
    logger.error(f"Model {model} not found in either OpenAI or Together models.")
    raise KeyError(f"Model {model} is not recognized in available models.")


# this function has been moved from openai.py to here because send_message could not be called in other modules.
@conditional_observe
async def call_model(
    sio_server,
    sid,
    messages: List[OpenAIMessage],
    model: str,
    client: AsyncOpenAI | AsyncAzureOpenAI,
    session_id: str,
    experiment_id: str,
    participant_id: Optional[str] = None,
    project_id: Optional[str] = None,
    stream: bool = True,
) -> OpenAIMessage:
    model = model.replace("together_ai-", "")  # for together call

    request_token_count, images_volume_total = calculate_limits(messages)
    # the token caps need an upper bound on what the provider counts, including
    # message overhead and images, not only the text
    prompt_estimate = estimate_prompt_tokens(messages, model)

    if request_token_count > token_count_limit:
        raise TokenError(
            f"Token limit of {request_token_count} for participant {participant_id} exceeded, total token count is {request_token_count}",
            request_token_count,
        )

    if images_volume_total > image_volume_limit:
        raise TokenError(
            f"Image volume limit of {images_volume_total} for participant {participant_id} exceeded, total token count is {images_volume_total}",
            images_volume_total,
        )

    # reserve the tokens this call may use before it starts, so that neither a
    # long reply nor concurrent calls can go past the project's token caps
    reservation = None
    if project_id is not None:
        project = await Project.find_one({"project_id": project_id})
        if project is not None:
            reservation, reason = await reserve_tokens(
                project, prompt_estimate, conversation_id=session_id
            )
            if reason:
                logger.info(f"Participant {participant_id} blocked by project limit: {reason}")
                await sio_server.emit(
                    "limit_reached", {"reason": reason, "message": limit_message(reason)}, sid
                )
                return "ExceptionError"  # the reply is not generated and not saved

    completion_kwargs = {}
    if reservation is not None and reservation.max_tokens is not None:
        completion_kwargs["max_tokens"] = reservation.max_tokens

    def completion_estimate_for(text: str) -> int:
        # the provider generates at most max_tokens, whatever tiktoken counts
        estimate = num_tokens_from_string(text)
        if completion_kwargs.get("max_tokens") is not None:
            estimate = min(estimate, completion_kwargs["max_tokens"])
        return estimate

    async def record_call_usage(completion_tokens: int):
        if project_id is None:
            return
        # streamed responses carry no `usage` with the pinned openai client,
        # so these counts are tiktoken estimates
        await record_usage(
            project_id=project_id,
            model=model,
            prompt_tokens=prompt_estimate,
            completion_tokens=completion_tokens,
            estimated=True,
            conversation_id=session_id,
            participant_id=participant_id,
        )

    status = "ok"
    response = None
    full_response = ""
    usage_recorded = False
    try:
        response = await completion_with_backoff(
            client,
            model=model,
            messages=messages,
            temperature=0.7,
            stream=stream,
            **completion_kwargs,
        )

        if stream:
            new_message = True
            async for chunk in response:
                if len(chunk.choices) == 0:
                    continue
                text_to_send_in_the_current_chunk = chunk.choices[0].delta.content or ""
                full_response += text_to_send_in_the_current_chunk

                response_data = {
                    "type": "message" if new_message else "stream",
                    "data": await create_message(
                        content=text_to_send_in_the_current_chunk,
                        role="assistant",
                    ),
                }
                new_message = False
                await sio_server.emit("message_to_client", response_data, sid)
        else:
            full_response = response.choices[0].message.content or ""
            response_data = {
                "type": "message",
                "data": await create_message(
                    content=full_response,
                    role="assistant",
                ),
            }
            await sio_server.emit("message_to_client", response_data, sid)

        response_token_count = num_tokens_from_string(full_response)
        total_token_count = request_token_count + response_token_count

        await record_call_usage(completion_estimate_for(full_response))
        usage_recorded = True

        if total_token_count > token_count_limit:
            raise TokenError(
                f"Token limit of {token_count_limit} for participant {participant_id} exceeded, total token count is {total_token_count}",
                total_token_count,
            )

        logger.debug(
            total_token_count, title=f"participant {participant_id} Total Token Count"
        )

        return full_response

    except Exception as e:
        status = "error"
        if response is not None and not usage_recorded:
            # The provider accepted the call, so it bills the prompt and the
            # reply streamed before the failure; record them and keep them
            # in the budgets instead of releasing the whole reservation.
            await record_call_usage(completion_estimate_for(full_response))
        response_data = {
            "type": "message",
            "data": await create_message(
                content=f"An error was occurred for client.chat.completions.create for participant_id {participant_id} : {e}",
                role="assistant",
            ),
        }
        await sio_server.emit("message_to_client", response_data, sid)

        return "ExceptionError"  # to make sure the flow of the program is not disrupted. this record will not be saved.

    finally:
        # The usage is recorded above; give back the reservation.
        await release_tokens(reservation)
        # Tell the client the assistant reply is complete (streamed or not).
        await sio_server.emit(
            "message_end", {"session_id": session_id, "status": status}, sid
        )


token_count_limit = 8000
image_volume_limit = 2000 * 1024  # the unit is byte (KB * 1024)


def calculate_limits(messages):
    request_token_count = 0
    images_volume_total = 0

    for message in messages:
        if isinstance(message["content"], list):
            for elem in message["content"]:
                if elem["type"] == "text":
                    request_token_count += num_tokens_from_string(elem["text"])

                if elem["type"] == "image_url":
                    response = requests.get(elem["image_url"]["url"])
                    if response.status_code == 200:
                        images_volume_total += len(response.content)
        else:
            request_token_count += num_tokens_from_string(message["content"])

    return request_token_count, images_volume_total


# Tokens a provider adds per message and to prime the reply.
MESSAGE_OVERHEAD_TOKENS = 4
REPLY_OVERHEAD_TOKENS = 3

# Text is counted with cl100k_base, the only encoding of the pinned tiktoken.
# It is exact for the GPT-4 and GPT-3.5 models; for other tokenizers the count
# is raised by a margin so that it stays an upper bound.
TEXT_MARGIN = {"gpt-4": 1.0, "gpt-4-turbo": 1.0, "gpt-3.5-turbo": 1.0}
OPENAI_TEXT_MARGIN = 1.1  # o200k_base (gpt-4o, gpt-4o-mini)
OTHER_TEXT_MARGIN = 1.25  # other providers' tokenizers

# Most tokens an image can cost: a high-detail image is scaled to at most
# 768 x 2048 pixels, which is 8 tiles of 512 pixels (base + 8 * per tile).
IMAGE_TOKENS = {
    "gpt-4o": 85 + 8 * 170,
    "gpt-4-turbo": 85 + 8 * 170,
    "gpt-4o-mini": 2833 + 8 * 5667,
}
DEFAULT_IMAGE_TOKENS = 85 + 8 * 170


def _text_margin(model: str) -> float:
    model = model.replace("together_ai-", "")
    if model in TEXT_MARGIN:
        return TEXT_MARGIN[model]
    return OPENAI_TEXT_MARGIN if model in models["openai"] else OTHER_TEXT_MARGIN


def estimate_prompt_tokens(messages: list, model: str, extra: str = "") -> int:
    """Upper bound on the prompt tokens a provider counts for these messages.

    Used to reserve token budget before a call, so it errs on the high side.
    """
    model = model.replace("together_ai-", "")
    text_tokens = num_tokens_from_string(extra)
    image_tokens = 0
    for message in messages:
        content = message.get("content") or ""
        if isinstance(content, list):
            for part in content:
                if part.get("type") == "text":
                    text_tokens += num_tokens_from_string(part.get("text", ""))
                elif part.get("type") == "image_url":
                    image_tokens += IMAGE_TOKENS.get(model, DEFAULT_IMAGE_TOKENS)
        else:
            text_tokens += num_tokens_from_string(str(content))

    overhead = REPLY_OVERHEAD_TOKENS + MESSAGE_OVERHEAD_TOKENS * len(messages)
    return math.ceil(text_tokens * _text_margin(model)) + image_tokens + overhead


def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


class TokenError(Exception):
    def __init__(self, message, token_count):
        super().__init__(message)
        self.token_count = token_count


def flush_langfuse():
    """
    Flush pending Langfuse events to ensure they are sent.
    This is useful in short-lived applications or at the end of request handling.
    Only flushes if Langfuse is enabled.
    """
    if langfuse_client:
        langfuse_client.flush()
