"""Sandbox file operations — confined to sandbox_dir."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import RunContext
from agent.core.deps import AgentDeps


async def sandbox_read(ctx: RunContext[AgentDeps], path: str) -> dict:
    """Read a file from the agent's sandbox working directory.

    Args:
        path: Relative path within the sandbox directory.
    """
    root = ctx.deps.sandbox_path()
    full = (root / path).resolve()
    if not str(full).startswith(str(root)):
        raise PermissionError(f"Path '{path}' escapes sandbox boundary")

    if not full.exists():
        return {"path": path, "exists": False, "content": None}

    content = full.read_text(encoding="utf-8")
    return {"path": path, "exists": True, "content": content, "size_bytes": len(content.encode())}


async def sandbox_write(ctx: RunContext[AgentDeps], path: str, content: str) -> dict:
    """Write a file to the agent's sandbox working directory.

    Args:
        path: Relative path within the sandbox directory.
        content: Content to write to the file.
    """
    root = ctx.deps.sandbox_path()
    full = (root / path).resolve()
    if not str(full).startswith(str(root)):
        raise PermissionError(f"Path '{path}' escapes sandbox boundary")

    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    return {"path": path, "written": True, "size_bytes": len(content.encode())}
