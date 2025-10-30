"""Main service classes for Natural Language to EQL conversion."""

from dataclasses import dataclass, field
from pathlib import Path
from .models import NaturalLanguageQuery, EQLQueryResult
from .validators import EQLQueryValidator
from .providers import LanguageModelProvider
from .prompt_builder import SystemPromptBuilder
from krrood.class_diagrams.class_diagram import ClassDiagram


@dataclass
class NaturalLanguageToEQLService:
    """
    Service for converting natural language to EQL queries.
    Follows Single Responsibility and Dependency Inversion principles.
    """
    
    provider: LanguageModelProvider
    validator: EQLQueryValidator
    
    def convert(self, text: str, class_diagram: ClassDiagram) -> EQLQueryResult:
        """
        Convert natural language to EQL query using ClassDiagram context.
        
        :param text: Natural language query description
        :param class_diagram: ClassDiagram containing entity types and schemas
        :return: Generated and validated EQL query
        """
        natural_query = NaturalLanguageQuery(
            text=text,
            class_diagram=class_diagram
        )
        
        result = self.provider.generate_eql(natural_query)
        
        validation_result = self.validator.validate(result.query_code)
        
        if not validation_result.is_valid:
            result.error_message = validation_result.error_message
            result.confidence = 0.0
        
        return result


@dataclass
class ConversationalEQLService:
    """
    Service for continuous natural language to EQL conversion with conversation history.
    Maintains context across multiple queries.
    """
    
    provider: LanguageModelProvider
    validator: EQLQueryValidator
    class_diagram: ClassDiagram
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    system_prompt: str = field(init=False, default="")
    
    def __post_init__(self):
        """Initialize system prompt."""
        prompt_builder = SystemPromptBuilder(self.class_diagram)
        self.system_prompt = prompt_builder.build_system_prompt()
    
    def convert(self, text: str) -> EQLQueryResult:
        """
        Convert natural language to EQL query with conversation context.
        
        :param text: Natural language query description
        :return: Generated and validated EQL query
        """
        natural_query = NaturalLanguageQuery(
            text=text,
            class_diagram=self.class_diagram
        )
        
        result = self.provider.generate_eql(natural_query)
        
        # Add to conversation history
        self.conversation_history.append({
            "user": text,
            "assistant": result.query_code,
            "confidence": str(result.confidence)
        })
        
        # Validate
        validation_result = self.validator.validate(result.query_code)
        
        if not validation_result.is_valid:
            result.error_message = validation_result.error_message
            result.confidence = 0.0
        
        return result
    
    def get_conversation_context(self) -> str:
        """
        Get formatted conversation history.
        
        :return: Formatted conversation history
        """
        lines = ["## Previous Queries\n"]
        for i, exchange in enumerate(self.conversation_history, 1):
            lines.append(f"### Query {i}")
            lines.append(f"User: {exchange['user']}")
            lines.append(f"```python\n{exchange['assistant']}\n```")
            lines.append("")
        
        return "\n".join(lines)
    
    def dump_system_prompt(self, file_path: str | Path):
        """
        Dump the system prompt to a file.
        
        :param file_path: Path where the system prompt will be saved
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            f.write(self.system_prompt)
    
    def dump_conversation(self, file_path: str | Path):
        """
        Dump the entire conversation including system prompt.
        
        :param file_path: Path where the conversation will be saved
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            f.write(self.system_prompt)
            f.write("\n\n" + "="*80 + "\n\n")
            f.write(self.get_conversation_context())
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
