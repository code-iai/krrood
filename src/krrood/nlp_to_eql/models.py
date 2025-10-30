"""Core data models for Natural Language to EQL conversion service."""

from dataclasses import dataclass, field
from krrood.class_diagrams.class_diagram import ClassDiagram


@dataclass
class NaturalLanguageQuery:
    """Represents a natural language query input with class diagram context."""
    
    text: str
    class_diagram: ClassDiagram


@dataclass
class EQLQueryResult:
    """Represents the generated EQL query and metadata."""
    
    query_code: str
    confidence: float
    extracted_entities: list[str]
    extracted_conditions: list[str]
    error_message: str = ""


@dataclass
class EQLExample:
    """Represents a single EQL query example with description."""
    
    description: str
    natural_language: str
    eql_code: str
    category: str


@dataclass
class ValidationResult:
    """Result of EQL query validation."""
    
    is_valid: bool
    error_message: str = ""
    syntax_errors: list[str] = field(default_factory=list)
