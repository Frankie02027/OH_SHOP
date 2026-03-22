from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    searxng_url: str = "http://searxng:8080"
    llm_base_url: str = "http://host.docker.internal:1234/v1"
    llm_model: str = "all-hands_openhands-lm-32b-v0.1"
    llm_api_key: str = "lm-studio"
    download_dir: Path = Path("/data/downloads")
    log_dir: Path = Path("/data/logs")
    mcp_port: int = 3010

    @classmethod
    def from_env(cls) -> "Settings":
        searxng_url = os.getenv("SEARXNG_URL", cls.searxng_url).rstrip("/")
        llm_base_url = os.getenv("LLM_BASE_URL", cls.llm_base_url).rstrip("/")
        llm_model = os.getenv("LLM_MODEL", cls.llm_model)
        llm_api_key = os.getenv("LLM_API_KEY", cls.llm_api_key)
        download_dir = Path(os.getenv("DOWNLOAD_DIR", str(cls.download_dir)))
        log_dir = Path(os.getenv("LOG_DIR", str(cls.log_dir)))
        mcp_port = int(os.getenv("MCP_PORT", str(cls.mcp_port)))
        if not (1 <= mcp_port <= 65535):
            raise ValueError("MCP_PORT must be in range 1..65535")

        return cls(
            searxng_url=searxng_url,
            llm_base_url=llm_base_url,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
            download_dir=download_dir,
            log_dir=log_dir,
            mcp_port=mcp_port,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
