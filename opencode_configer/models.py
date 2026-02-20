"""
Pydantic models for opencode-configer API request/response shapes.
"""
from typing import Any

from pydantic import BaseModel, Field


class ModelEntry(BaseModel):
    """
    A single model entry within a provider's models dict.

    :param options: Arbitrary model-level options.
    :param limit: Optional context/output token limits.
    """

    options: dict[str, Any] = Field(default_factory=dict)
    limit: dict[str, Any] | None = None


class ProviderOptions(BaseModel):
    """
    Provider-level connection options.

    :param api_key: Optional API key for authentication.
    :param base_url: Optional base URL for OpenAI-compatible endpoints.
    """

    apiKey: str | None = None
    baseURL: str | None = None

    model_config = {"extra": "allow"}


class ProviderConfig(BaseModel):
    """
    Configuration for a single opencode provider.

    :param name: Display name of the provider.
    :param npm: npm package to use for the provider.
    :param models: Dict of model ID to model entry.
    :param options: Provider connection options.
    :param whitelist: Optional model ID whitelist.
    :param blacklist: Optional model ID blacklist.
    """

    name: str | None = None
    npm: str | None = None
    models: dict[str, ModelEntry] = Field(default_factory=dict)
    options: ProviderOptions = Field(default_factory=ProviderOptions)
    whitelist: list[str] | None = None
    blacklist: list[str] | None = None

    model_config = {"extra": "allow"}


class OpencodeConfig(BaseModel):
    """
    Top-level opencode config.json structure (partial — only fields we manage).

    :param schema: JSON schema URL.
    :param provider: Dict of provider name to provider config.
    :param enabled_providers: Optional list of explicitly enabled providers.
    """

    schema_url: str | None = Field(default=None, alias="$schema")
    provider: dict[str, ProviderConfig] = Field(default_factory=dict)
    enabled_providers: list[str] | None = None

    model_config = {"populate_by_name": True, "extra": "allow"}


class AgentConfig(BaseModel):
    """
    oh-my-opencode per-agent configuration.

    :param model: Model identifier in provider/model format.
    """

    model: str | None = None

    model_config = {"extra": "allow"}


class CategoryConfig(BaseModel):
    """
    oh-my-opencode per-category configuration.

    :param model: Model identifier in provider/model format.
    :param variant: Optional model variant.
    """

    model: str | None = None
    variant: str | None = None

    model_config = {"extra": "allow"}


class OhMyOpencodeConfig(BaseModel):
    """
    oh-my-opencode.json structure (partial — only model-related fields).

    :param schema_url: JSON schema URL.
    :param model: Default top-level model.
    :param agents: Per-agent model overrides.
    :param categories: Per-category model overrides.
    """

    schema_url: str | None = Field(default=None, alias="$schema")
    model: str | None = None
    agents: dict[str, AgentConfig] = Field(default_factory=dict)
    categories: dict[str, CategoryConfig] = Field(default_factory=dict)

    model_config = {"populate_by_name": True, "extra": "allow"}


class FetchModelsRequest(BaseModel):
    """
    Request body for fetching models from a provider's /v1/models endpoint.

    :param base_url: The provider's base URL.
    :param api_key: Optional API key.
    """

    base_url: str
    api_key: str | None = None


class DiscoveredModel(BaseModel):
    """
    A model returned by a provider's /v1/models endpoint.

    :param id: Model identifier.
    :param enabled: Whether the model is currently in the config.
    :param existing_entry: Existing config entry for this model, if any.
    """

    id: str
    enabled: bool = False
    existing_entry: ModelEntry | None = None


class ConfigSet(BaseModel):
    """
    Metadata for a saved config set.

    :param name: Name of the set (directory name).
    :param has_opencode: Whether the set contains a config.json.
    :param has_oh_my_opencode: Whether the set contains an oh-my-opencode.json.
    """

    name: str
    has_opencode: bool = False
    has_oh_my_opencode: bool = False


class SaveSetRequest(BaseModel):
    """
    Request body for saving a config set.

    :param opencode_config: The opencode config.json content as a dict.
    :param oh_my_opencode_config: The oh-my-opencode.json content as a dict.
    """

    opencode_config: dict[str, Any]
    oh_my_opencode_config: dict[str, Any]


class ApplyRequest(BaseModel):
    """
    Request body for applying configs directly (without a named set).

    :param opencode_config: The opencode config.json content as a dict.
    :param oh_my_opencode_config: The oh-my-opencode.json content as a dict.
    """

    opencode_config: dict[str, Any]
    oh_my_opencode_config: dict[str, Any]
