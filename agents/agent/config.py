"""Configuration — loads from YAML, validates with Pydantic.

This file is ONLY config schema + loading. No runtime state.
Source of truth: config/agent_config.yaml
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ConfigError(Exception):
    pass


class LLMProviderConfig(BaseModel):
    model: str
    base_url: str = ""
    api_key_env: str = ""

    # Snowflake Cortex-specific (only used when provider is "cortex")
    snowflake_connection_name: str = ""
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_authenticator: str = "externalbrowser"
    snowflake_role: str = ""
    snowflake_warehouse: str = ""

    def resolve_api_key(self) -> str:
        if not self.api_key_env:
            return ""
        return os.environ.get(self.api_key_env, "")


class LLMConfig(BaseModel):
    active_provider: str = "test"
    temperature: float = 0.0
    max_tokens: int = 4096
    thinking_budget: int = 10000
    providers: dict[str, LLMProviderConfig] = Field(default_factory=dict)

    def get_provider(self, name: str) -> LLMProviderConfig:
        if name not in self.providers:
            raise ConfigError(
                f"Provider '{name}' not in config. "
                f"Available: {list(self.providers.keys())}"
            )
        return self.providers[name]


class RobotConfig(BaseModel):
    host: str = "localhost"
    port: int = 50051
    timeout_seconds: int = 30


class PerceptionConfig(BaseModel):
    camera_type: str = "zebra"
    camera_host: str = "localhost"
    camera_port: int = 8080


class MCPConfig(BaseModel):
    servers: list[dict[str, Any]] = Field(default_factory=list)


class ToolsConfig(BaseModel):
    mock_mode: bool = True
    mock_delay: float = 2.0
    mock_scenario: str = "premature_harvest"
    robot_stream_url: str = ""
    robot: RobotConfig = Field(default_factory=RobotConfig)
    perception: PerceptionConfig = Field(default_factory=PerceptionConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )


class AgentCoreConfig(BaseModel):
    name: str = "CellCultureAgent"
    max_iterations: int = 20
    sandbox_dir: str = "./sandbox"
    working_dir: str = "./workspace"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "structured"


class AppConfig(BaseModel):
    agent: AgentCoreConfig = Field(default_factory=AgentCoreConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(path: str | Path | None = None) -> AppConfig:
    if path is None:
        path = os.environ.get("AGENT_CONFIG_PATH", "config/agent_config.yaml")
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path.resolve()}")
    with open(path) as f:
        raw = yaml.safe_load(f)
    if raw is None:
        raise ConfigError(f"Config file is empty: {path.resolve()}")
    return AppConfig.model_validate(raw)
