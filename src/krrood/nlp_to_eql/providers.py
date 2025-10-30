"""LLM providers for Natural Language to EQL conversion."""

from dataclasses import dataclass, field
from typing import Protocol
from pathlib import Path
from .models import NaturalLanguageQuery, EQLQueryResult
from .prompt_builder import SystemPromptBuilder


class LanguageModelProvider(Protocol):
    """Protocol for language model providers that can generate EQL queries."""
    
    def generate_eql(self, natural_query: NaturalLanguageQuery) -> EQLQueryResult:
        """
        Generate an EQL query from natural language description.
        
        :param natural_query: The natural language query with ClassDiagram context
        :return: Generated EQL query result with metadata
        """
        ...


@dataclass
class OpenAIEQLProvider:
    """Generates EQL queries using OpenAI's GPT models."""
    
    api_key: str
    model: str = "gpt-4"
    prompt_builder: SystemPromptBuilder = field(init=False, default=None)
    
    def __post_init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Install it with: pip install openai"
            )
    
    def generate_eql(self, natural_query: NaturalLanguageQuery) -> EQLQueryResult:
        """
        Generate EQL query using OpenAI GPT models.
        
        :param natural_query: Natural language query with ClassDiagram context
        :return: Generated EQL query result
        """
        self.prompt_builder = SystemPromptBuilder(natural_query.class_diagram)
        system_prompt = self.prompt_builder.build_system_prompt()
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": natural_query.text}
            ],
            temperature=0.1
        )
        
        return self._parse_response(response)
    
    def dump_system_prompt(self, file_path: str | Path):
        """
        Dump the current system prompt to a file.
        
        :param file_path: Path where the system prompt will be saved
        """
        if self.prompt_builder is None:
            raise ValueError("No system prompt available. Call generate_eql first.")
        
        self.prompt_builder.dump_to_file(file_path)
    
    def _parse_response(self, response) -> EQLQueryResult:
        """
        Parse OpenAI response into EQL query result.
        
        :param response: OpenAI API response
        :return: Parsed EQL query result
        """
        content = response.choices[0].message.content
        
        # Extract code from markdown code blocks if present
        if "```python" in content:
            code = content.split("```python")[1].split("```")[0].strip()
        elif "```" in content:
            code = content.split("```")[1].split("```")[0].strip()
        else:
            code = content.strip()
        
        from .formatters import SchemaContextFormatter
        formatter = SchemaContextFormatter(self.prompt_builder.class_diagram)
        
        return EQLQueryResult(
            query_code=code,
            confidence=0.9,
            extracted_entities=formatter.get_class_names(),
            extracted_conditions=[]
        )


@dataclass
class ClaudeEQLProvider:
    """Generates EQL queries using Anthropic's Claude models."""
    
    api_key: str
    model: str = "claude-3-5-sonnet-20241022"
    prompt_builder: SystemPromptBuilder = field(init=False, default=None)
    
    def __post_init__(self):
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "Anthropic package not installed. Install it with: pip install anthropic"
            )
    
    def generate_eql(self, natural_query: NaturalLanguageQuery) -> EQLQueryResult:
        """
        Generate EQL query using Claude.
        
        :param natural_query: Natural language query with ClassDiagram context
        :return: Generated EQL query result
        """
        self.prompt_builder = SystemPromptBuilder(natural_query.class_diagram)
        
        system_prompt = self._get_system_prompt()
        user_prompt = natural_query.text
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        
        return self._parse_response(response)
    
    def _get_system_prompt(self) -> str:
        """Build system prompt for Claude."""
        return self.prompt_builder.build_system_prompt()
    
    def dump_system_prompt(self, file_path: str | Path):
        """
        Dump the current system prompt to a file.
        
        :param file_path: Path where the system prompt will be saved
        """
        if self.prompt_builder is None:
            raise ValueError("No system prompt available. Call generate_eql first.")
        
        self.prompt_builder.dump_to_file(file_path)
    
    def _parse_response(self, response) -> EQLQueryResult:
        """
        Parse Claude response into EQL query result.
        
        :param response: Claude API response
        :return: Parsed EQL query result
        """
        content = response.content[0].text
        
        # Extract code from markdown code blocks if present
        if "```python" in content:
            code = content.split("```python")[1].split("```")[0].strip()
        elif "```" in content:
            code = content.split("```")[1].split("```")[0].strip()
        else:
            code = content.strip()
        
        from .formatters import SchemaContextFormatter
        formatter = SchemaContextFormatter(self.prompt_builder.class_diagram)
        
        return EQLQueryResult(
            query_code=code,
            confidence=0.9,
            extracted_entities=formatter.get_class_names(),
            extracted_conditions=[]
        )


@dataclass
class OllamaEQLProvider:
    """Generates EQL queries using local Ollama models."""
    
    base_url: str = "http://localhost:11434"
    model: str = "llama3.1"
    prompt_builder: SystemPromptBuilder = field(init=False, default=None)
    
    def generate_eql(self, natural_query: NaturalLanguageQuery) -> EQLQueryResult:
        """
        Generate EQL query using Ollama local LLM.
        
        :param natural_query: Natural language query with ClassDiagram context
        :return: Generated EQL query result
        """
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests package not installed. Install it with: pip install requests"
            )
        
        self.prompt_builder = SystemPromptBuilder(natural_query.class_diagram)
        prompt = self._build_full_prompt(natural_query)
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        return self._parse_response(response.json())
    
    def _build_full_prompt(self, natural_query: NaturalLanguageQuery) -> str:
        """Build full prompt combining system and user prompts."""
        system_prompt = self.prompt_builder.build_system_prompt()
        return f"{system_prompt}\n\nUser Query: {natural_query.text}\n\nGenerate EQL code:"
    
    def dump_system_prompt(self, file_path: str | Path):
        """
        Dump the current system prompt to a file.
        
        :param file_path: Path where the system prompt will be saved
        """
        if self.prompt_builder is None:
            raise ValueError("No system prompt available. Call generate_eql first.")
        
        self.prompt_builder.dump_to_file(file_path)
    
    def _parse_response(self, response_json: dict) -> EQLQueryResult:
        """
        Parse Ollama response into EQL query result.
        
        :param response_json: Ollama API response JSON
        :return: Parsed EQL query result
        """
        content = response_json.get("response", "")
        
        # Extract code from markdown code blocks if present
        if "```python" in content:
            code = content.split("```python")[1].split("```")[0].strip()
        elif "```" in content:
            code = content.split("```")[1].split("```")[0].strip()
        else:
            code = content.strip()
        
        from .formatters import SchemaContextFormatter
        formatter = SchemaContextFormatter(self.prompt_builder.class_diagram)
        
        return EQLQueryResult(
            query_code=code,
            confidence=0.7,  # Lower confidence for local models
            extracted_entities=formatter.get_class_names(),
            extracted_conditions=[]
        )
