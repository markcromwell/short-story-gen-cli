"""Configuration management for editorial workflow."""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Configuration loading error."""

    pass


class ConfigManager:
    """Manages configuration for the editorial system."""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or Path(__file__).parent.parent.parent.parent / "config"
        self._config_cache: dict[str, dict[str, Any]] = {}

    def load_editorial_config(self) -> dict[str, Any]:
        """Load editorial-specific configuration."""
        return self._load_config("editorial_config.yaml")

    def load_main_config(self) -> dict[str, Any]:
        """Load main application configuration."""
        # Try to load from existing config files
        config_files = ["config.yaml", "settings.yaml", "app_config.yaml"]

        for config_file in config_files:
            try:
                return self._load_config(config_file)
            except ConfigError:
                continue

        # Return default config if no config file found
        return self._get_default_config()

    def _load_config(self, filename: str) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if filename in self._config_cache:
            return self._config_cache[filename]

        config_path = self.config_dir / filename

        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                self._config_cache[filename] = config
                return config
        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {config_path}: {e}")

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration values."""
        return {
            "models": {
                "default": "xai/grok-4-fast-reasoning",
                "ollama": {
                    "base_url": "http://localhost:11434",
                    "timeout": 120,
                    "supported_models": ["qwen3:30b"],
                },
                "openai": {
                    "api_key_env": "OPENAI_API_KEY",
                    "timeout": 60,
                    "supported_models": ["gpt-4o", "gpt-4o-mini"],
                },
                "xai": {
                    "api_key_env": "XAI_API_KEY",
                    "timeout": 60,
                    "supported_models": ["grok-4-fast-reasoning", "grok-2-1212", "grok-beta"],
                },
            },
            "editorial": {
                "enabled": True,
                "cost_control": {"enabled": True, "default_budget": 5.00, "alert_threshold": 0.80},
                "editors": {
                    "idea": {
                        "enabled": True,
                        "default_model": "ollama/qwen3:30b",
                        "max_retries": 3,
                        "timeout_seconds": 300,
                    },
                    "content": {
                        "enabled": True,
                        "default_model": "ollama/qwen3:30b",
                        "batch_size": 5,
                        "max_concurrent_batches": 3,
                    },
                },
            },
            "logging": {
                "level": "INFO",
                "file": "logs/editorial.log",
                "max_file_size": "10MB",
                "retention_days": 30,
            },
        }

    def get_editorial_config(self) -> dict[str, Any]:
        """Get complete editorial configuration."""
        main_config = self.load_main_config()

        # Try to load editorial-specific config
        try:
            editorial_config = self.load_editorial_config()
            # Merge with main config
            if "editorial" not in main_config:
                main_config["editorial"] = {}
            main_config["editorial"].update(editorial_config)
        except ConfigError:
            # Use print instead of logger to avoid logging issues during config loading
            print("Warning: Editorial config file not found, using defaults")

        return main_config.get("editorial", self._get_default_config()["editorial"])  # type: ignore[no-any-return]

    def get_model_config(self, model_name: str | None = None) -> dict[str, Any]:
        """Get model configuration."""
        config = self.load_main_config()
        models_config = config.get("models", {})

        if model_name:
            # Return config for specific model
            for provider, provider_config in models_config.items():
                if provider == "default":
                    continue
                if model_name in provider_config.get("supported_models", []):
                    return {"provider": provider, "model": model_name, **provider_config}  # type: ignore[no-any-return]
            # Model not found, return default
            return {
                "provider": "ollama",
                "model": models_config.get("default", "ollama/qwen3:30b"),
                **models_config.get("ollama", {}),
            }  # type: ignore[no-any-return]

        return models_config  # type: ignore[no-any-return]

    def get_logging_config(self) -> dict[str, Any]:
        """Get logging configuration."""
        config = self.load_main_config()
        return config.get("logging", {"level": "INFO", "file": "logs/editorial.log"})  # type: ignore[no-any-return]


# Global config manager instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_config() -> dict[str, Any]:
    """Load complete configuration."""
    return get_config_manager().load_main_config()


def load_editorial_config() -> dict[str, Any]:
    """Load editorial-specific configuration."""
    return get_config_manager().get_editorial_config()
