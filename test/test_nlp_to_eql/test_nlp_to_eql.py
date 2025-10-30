"""Comprehensive tests for Natural Language to EQL conversion service."""

import pytest
from dataclasses import dataclass
from pathlib import Path
from krrood.entity_query_language.entity import Symbol
from krrood.class_diagrams.class_diagram import ClassDiagram
from krrood.nlp_to_eql import (
    NaturalLanguageQuery,
    EQLQueryResult,
    EQLExample,
    ValidationResult,
    SchemaContextFormatter,
    EQLQueryValidator,
    SystemPromptBuilder,
)


# Test fixtures
@dataclass
class Body(Symbol):
    """Test body class."""
    name: str


@dataclass
class Connection(Symbol):
    """Test connection class."""
    parent: Body
    child: Body


@dataclass
class PrismaticConnection(Connection):
    """Test prismatic connection class."""
    pass


@dataclass
class FixedConnection(Connection):
    """Test fixed connection class."""
    pass


@pytest.fixture
def simple_class_diagram():
    """Fixture providing a simple ClassDiagram for testing."""
    classes = [Body, Connection, PrismaticConnection, FixedConnection]
    return ClassDiagram(classes)


@pytest.fixture
def validator():
    """Fixture providing an EQL query validator."""
    return EQLQueryValidator()


@pytest.fixture
def prompt_builder(simple_class_diagram):
    """Fixture providing a system prompt builder."""
    return SystemPromptBuilder(simple_class_diagram)


# Tests for EQLQueryValidator
class TestEQLQueryValidator:
    """Tests for EQL query validator."""
    
    def test_validate_valid_query(self, validator):
        """Test validation of a valid EQL query."""
        valid_query = """
with symbolic_mode():
    body = let(Body, domain=bodies)
    query = an(entity(body, body.name == "Test"))
"""
        result = validator.validate(valid_query)
        
        assert result.is_valid
        assert result.error_message == ""
        assert len(result.syntax_errors) == 0
    
    def test_validate_query_without_symbolic_mode(self, validator):
        """Test validation fails when symbolic_mode is missing."""
        invalid_query = """
body = let(Body, domain=bodies)
query = an(entity(body, body.name == "Test"))
"""
        result = validator.validate(invalid_query)
        
        assert not result.is_valid
        assert "symbolic_mode" in result.error_message
    
    def test_validate_query_without_quantifier(self, validator):
        """Test validation fails when quantifier is missing."""
        invalid_query = """
with symbolic_mode():
    body = let(Body, domain=bodies)
"""
        result = validator.validate(invalid_query)
        
        assert not result.is_valid
        assert "quantifier" in result.error_message
    
    def test_validate_query_with_syntax_error(self, validator):
        """Test validation fails with syntax errors."""
        invalid_query = """
with symbolic_mode():
    body = let(Body, domain=bodies
    query = an(entity(body))
"""
        result = validator.validate(invalid_query)
        
        assert not result.is_valid
        assert "Syntax error" in result.error_message
        assert len(result.syntax_errors) > 0


# Tests for SchemaContextFormatter
class TestSchemaContextFormatter:
    """Tests for schema context formatter."""
    
    def test_format_for_prompt(self, simple_class_diagram):
        """Test formatting class diagram for prompt."""
        formatter = SchemaContextFormatter(simple_class_diagram)
        schema_text = formatter.format_for_prompt()
        
        assert "Body" in schema_text
        assert "Connection" in schema_text
        assert "PrismaticConnection" in schema_text
        assert "FixedConnection" in schema_text
        assert "name" in schema_text
        assert "parent" in schema_text
        assert "child" in schema_text
    
    def test_get_class_names(self, simple_class_diagram):
        """Test retrieving class names."""
        formatter = SchemaContextFormatter(simple_class_diagram)
        class_names = formatter.get_class_names()
        
        assert "Body" in class_names
        assert "Connection" in class_names
        assert "PrismaticConnection" in class_names
        assert "FixedConnection" in class_names
        assert len(class_names) == 4
    
    def test_get_classes_map(self, simple_class_diagram):
        """Test retrieving classes map."""
        formatter = SchemaContextFormatter(simple_class_diagram)
        classes_map = formatter.get_classes_map()
        
        assert classes_map["Body"] == Body
        assert classes_map["Connection"] == Connection
        assert classes_map["PrismaticConnection"] == PrismaticConnection
        assert classes_map["FixedConnection"] == FixedConnection
    
    def test_format_includes_relationships(self, simple_class_diagram):
        """Test that formatting includes relationship information."""
        formatter = SchemaContextFormatter(simple_class_diagram)
        schema_text = formatter.format_for_prompt()
        
        # Check for relationship section
        assert "Relationships:" in schema_text or "parent" in schema_text
    
    def test_format_includes_inheritance(self, simple_class_diagram):
        """Test that formatting includes inheritance information."""
        formatter = SchemaContextFormatter(simple_class_diagram)
        schema_text = formatter.format_for_prompt()
        
        # Check for inheritance section or inheritance relationships
        assert "Inheritance:" in schema_text or "inherits from" in schema_text
    
    def test_format_as_pyi(self, simple_class_diagram):
        """Test formatting class diagram as .pyi stub file."""
        formatter = SchemaContextFormatter(simple_class_diagram)
        pyi_content = formatter.format_as_pyi()
        
        # Check for proper stub file structure
        assert '"""Type stubs for entity classes."""' in pyi_content
        assert "from dataclasses import dataclass" in pyi_content
        assert "from typing import Optional" in pyi_content
        
        # Check for class definitions
        assert "@dataclass" in pyi_content
        assert "class Body:" in pyi_content
        assert "class Connection:" in pyi_content
        
        # Check for fields
        assert "name: str" in pyi_content
        assert "parent: Body" in pyi_content
        assert "child: Body" in pyi_content
    
    def test_format_as_pyi_with_inheritance(self, simple_class_diagram):
        """Test that .pyi format includes inheritance."""
        formatter = SchemaContextFormatter(simple_class_diagram)
        pyi_content = formatter.format_as_pyi()
        
        # Check for inheritance syntax
        assert "class PrismaticConnection(Connection):" in pyi_content
        assert "class FixedConnection(Connection):" in pyi_content
    
    def test_format_as_pyi_handles_empty_classes(self, simple_class_diagram):
        """Test that .pyi format handles classes with no fields."""
        formatter = SchemaContextFormatter(simple_class_diagram)
        pyi_content = formatter.format_as_pyi()
        
        # Check that classes without fields have 'pass'
        # PrismaticConnection and FixedConnection inherit fields but don't define new ones
        assert "pass" in pyi_content


# Tests for SystemPromptBuilder
class TestSystemPromptBuilder:
    """Tests for system prompt builder."""
    
    def test_build_system_prompt(self, prompt_builder):
        """Test building complete system prompt."""
        prompt = prompt_builder.build_system_prompt()
        
        assert "EQL Query Generation Assistant" in prompt
        assert "EQL Syntax Rules" in prompt
        assert "EQL API Reference" in prompt
        assert "EQL Query Examples" in prompt
        assert "Available Entity Types" in prompt
        assert "Output Format Requirements" in prompt
    
    def test_build_prompt_includes_schema(self, prompt_builder):
        """Test that prompt includes schema information."""
        prompt = prompt_builder.build_system_prompt()
        
        assert "Body" in prompt
        assert "Connection" in prompt
        assert "PrismaticConnection" in prompt
    
    def test_add_custom_example(self, prompt_builder):
        """Test adding custom examples."""
        prompt_builder.add_example(
            description="Test example",
            natural_language="Find test entities",
            eql_code="with symbolic_mode():\n    query = an(...)",
            category="custom"
        )
        
        prompt = prompt_builder.build_system_prompt()
        assert "Test example" in prompt
        assert "Find test entities" in prompt
    
    def test_examples_grouped_by_category(self, prompt_builder):
        """Test that examples are grouped by category."""
        prompt_builder.add_example(
            description="Filter example",
            natural_language="Filter by name",
            eql_code="...",
            category="filtering"
        )
        prompt_builder.add_example(
            description="Join example",
            natural_language="Join tables",
            eql_code="...",
            category="joins"
        )
        
        prompt = prompt_builder.build_system_prompt()
        # Check that categories appear in the prompt
        assert "Filtering" in prompt or "filtering" in prompt
        assert "Joins" in prompt or "joins" in prompt
    
    def test_dump_to_file(self, prompt_builder, tmp_path):
        """Test dumping system prompt to file."""
        output_file = tmp_path / "test_prompt.md"
        prompt_builder.dump_to_file(output_file)
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "EQL Query Generation Assistant" in content
        assert len(content) > 1000
    
    def test_prompt_includes_pyi_interface(self, prompt_builder):
        """Test that system prompt includes .pyi interface section."""
        prompt = prompt_builder.build_system_prompt()
        
        # Check for .pyi section header
        assert "Python Type Interface (.pyi)" in prompt
        
        # Check for .pyi content markers
        assert "@dataclass" in prompt
        assert "class Body:" in prompt
        assert "class Connection:" in prompt
        assert "name: str" in prompt
        
        # Check that it's in a code block
        assert "```python" in prompt


# Tests for NaturalLanguageQuery model
class TestNaturalLanguageQuery:
    """Tests for natural language query model."""
    
    def test_create_query(self, simple_class_diagram):
        """Test creating a natural language query."""
        query = NaturalLanguageQuery(
            text="Find all bodies",
            class_diagram=simple_class_diagram
        )
        
        assert query.text == "Find all bodies"
        assert query.class_diagram == simple_class_diagram


# Tests for EQLQueryResult model
class TestEQLQueryResult:
    """Tests for EQL query result model."""
    
    def test_create_result(self):
        """Test creating an EQL query result."""
        result = EQLQueryResult(
            query_code="test code",
            confidence=0.9,
            extracted_entities=["Body"],
            extracted_conditions=["name == 'Test'"]
        )
        
        assert result.query_code == "test code"
        assert result.confidence == 0.9
        assert "Body" in result.extracted_entities
        assert result.error_message == ""
    
    def test_result_with_error(self):
        """Test creating result with error."""
        result = EQLQueryResult(
            query_code="invalid",
            confidence=0.0,
            extracted_entities=[],
            extracted_conditions=[],
            error_message="Validation failed"
        )
        
        assert result.confidence == 0.0
        assert result.error_message == "Validation failed"


# Tests for EQLExample model
class TestEQLExample:
    """Tests for EQL example model."""
    
    def test_create_example(self):
        """Test creating an EQL example."""
        example = EQLExample(
            description="Test example",
            natural_language="Find bodies",
            eql_code="with symbolic_mode(): ...",
            category="filtering"
        )
        
        assert example.description == "Test example"
        assert example.natural_language == "Find bodies"
        assert "symbolic_mode" in example.eql_code
        assert example.category == "filtering"


# Tests for ValidationResult model
class TestValidationResult:
    """Tests for validation result model."""
    
    def test_valid_result(self):
        """Test creating a valid validation result."""
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid
        assert result.error_message == ""
        assert len(result.syntax_errors) == 0
    
    def test_invalid_result(self):
        """Test creating an invalid validation result."""
        result = ValidationResult(
            is_valid=False,
            error_message="Error occurred",
            syntax_errors=["Syntax error 1"]
        )
        
        assert not result.is_valid
        assert result.error_message == "Error occurred"
        assert "Syntax error 1" in result.syntax_errors


# Integration tests
class TestIntegration:
    """Integration tests for the complete workflow."""
    
    def test_complete_prompt_generation_workflow(self, simple_class_diagram, tmp_path):
        """Test complete workflow from ClassDiagram to prompt file."""
        # Create prompt builder
        builder = SystemPromptBuilder(simple_class_diagram)
        
        # Add custom example
        builder.add_example(
            description="Integration test example",
            natural_language="Test query",
            eql_code="test code",
            category="test"
        )
        
        # Build prompt
        prompt = builder.build_system_prompt()
        assert len(prompt) > 1000
        
        # Dump to file
        output_file = tmp_path / "integration_test_prompt.md"
        builder.dump_to_file(output_file)
        
        # Verify file
        assert output_file.exists()
        content = output_file.read_text()
        assert content == prompt
        assert "Integration test example" in content
