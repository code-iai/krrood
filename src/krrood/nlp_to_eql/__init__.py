"""Natural Language to EQL conversion service."""

from .models import (
    NaturalLanguageQuery,
    EQLQueryResult,
    EQLExample,
    ValidationResult,
)
from .formatters import SchemaContextFormatter
from .validators import EQLQueryValidator
from .prompt_builder import SystemPromptBuilder
from .providers import (
    LanguageModelProvider,
    OpenAIEQLProvider,
    ClaudeEQLProvider,
    OllamaEQLProvider,
)
from .service import (
    NaturalLanguageToEQLService,
    ConversationalEQLService,
)

__all__ = [
    # Core models
    "NaturalLanguageQuery",
    "EQLQueryResult",
    "EQLExample",
    "ValidationResult",
    # Formatters
    "SchemaContextFormatter",
    # Validators
    "EQLQueryValidator",
    # Prompt builder
    "SystemPromptBuilder",
    # Providers
    "LanguageModelProvider",
    "OpenAIEQLProvider",
    "ClaudeEQLProvider",
    "OllamaEQLProvider",
    # Services
    "NaturalLanguageToEQLService",
    "ConversationalEQLService",
]
