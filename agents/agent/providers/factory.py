"""LLM provider factory — creates PydanticAI model from config.

Supports: test, openai, anthropic, openrouter, cortex.
To add a new provider: add to agent_config.yaml, add elif branch here.
"""

from __future__ import annotations

from typing import Union

from pydantic_ai.models import Model

from agent.config import AppConfig, ConfigError


def create_model(provider_name: str, config: AppConfig) -> Union[str, Model]:
    provider_cfg = config.llm.get_provider(provider_name)

    if provider_name == "test":
        from agent.providers.mock import create_mock_model
        return create_mock_model(config.tools.mock_scenario)

    if provider_name == "openai":
        return f"openai:{provider_cfg.model}"

    if provider_name == "anthropic":
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.providers.anthropic import AnthropicProvider

        api_key = provider_cfg.resolve_api_key()
        if not api_key:
            raise ConfigError(
                f"Provider 'anthropic' requires API key. "
                f"Set env var: {provider_cfg.api_key_env}"
            )
        return AnthropicModel(
            provider_cfg.model,
            provider=AnthropicProvider(api_key=api_key),
        )

    if provider_name == "openrouter":
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider

        api_key = provider_cfg.resolve_api_key()
        if not api_key:
            raise ConfigError(
                f"Provider 'openrouter' requires API key. "
                f"Set env var: {provider_cfg.api_key_env}"
            )
        return OpenAIModel(
            provider_cfg.model,
            provider=OpenAIProvider(
                base_url=provider_cfg.base_url,
                api_key=api_key,
            ),
        )

    if provider_name == "cortex":
        from agent.providers.cortex import create_cortex_model

        if not provider_cfg.snowflake_connection_name and not provider_cfg.snowflake_account:
            raise ConfigError(
                "Provider 'cortex' requires snowflake_connection_name or snowflake_account in config."
            )
        return create_cortex_model(provider_cfg)

    raise ConfigError(
        f"Unknown provider '{provider_name}'. "
        f"Supported: test, openai, anthropic, openrouter, cortex"
    )
