"""
Demo script for Natural Language to EQL system prompt generation.

This script demonstrates:
1. Creating a ClassDiagram from domain models
2. Building a comprehensive system prompt with EQL examples
3. Adding custom examples to the prompt
4. Dumping the system prompt to a file
"""

from dataclasses import dataclass
from pathlib import Path
from krrood.entity_query_language.entity import Symbol
from krrood.class_diagrams.class_diagram import ClassDiagram
from krrood.nlp_to_eql import SystemPromptBuilder


# Define example domain models
@dataclass
class Body(Symbol):
    """Represents a physical body in a kinematic system."""
    name: str


@dataclass
class Connection(Symbol):
    """Represents a connection between two bodies."""
    parent: Body
    child: Body


@dataclass
class PrismaticConnection(Connection):
    """Represents a prismatic (sliding) connection."""
    pass


@dataclass
class FixedConnection(Connection):
    """Represents a fixed connection."""
    pass


@dataclass
class RevoluteConnection(Connection):
    """Represents a revolute (rotating) connection."""
    pass


def main():
    """Main demo function."""
    print("=" * 80)
    print("Natural Language to EQL System Prompt Generation Demo")
    print("=" * 80)
    print()
    
    # Step 1: Create ClassDiagram from domain models
    print("Step 1: Creating ClassDiagram from domain models...")
    classes = [Body, Connection, PrismaticConnection, FixedConnection, RevoluteConnection]
    class_diagram = ClassDiagram(classes)
    print(f"  ✓ Created ClassDiagram with {len(classes)} classes")
    print()
    
    # Step 2: Create SystemPromptBuilder
    print("Step 2: Creating SystemPromptBuilder...")
    prompt_builder = SystemPromptBuilder(class_diagram)
    print("  ✓ SystemPromptBuilder created with default examples")
    print()
    
    # Step 3: Add custom examples
    print("Step 3: Adding custom domain-specific examples...")
    
    prompt_builder.add_example(
        description="Find all prismatic connections",
        natural_language="Find all prismatic connections in the system",
        eql_code="""with symbolic_mode():
    connection = let(PrismaticConnection, domain=world.connections)
    query = an(entity(connection))
results = query.evaluate()""",
        category="type_filtering"
    )
    
    prompt_builder.add_example(
        description="Find connections by parent body name",
        natural_language="Find all connections where the parent body name starts with 'Container'",
        eql_code="""with symbolic_mode():
    connection = let(Connection, domain=world.connections)
    query = an(entity(connection, connection.parent.name.startswith("Container")))
results = query.evaluate()""",
        category="relationship_filtering"
    )
    
    prompt_builder.add_example(
        description="Complex kinematic chain query",
        natural_language="Find all kinematic chains where a prismatic connection's child is a fixed connection's parent",
        eql_code="""with symbolic_mode():
    prismatic = let(PrismaticConnection, domain=world.connections)
    fixed = let(FixedConnection, domain=world.connections)
    query = an(set_of(
        (prismatic, fixed),
        fixed.parent == prismatic.child
    ))
results = query.evaluate()""",
        category="complex_queries"
    )
    
    print(f"  ✓ Added 3 custom examples")
    print()
    
    # Step 4: Generate system prompt
    print("Step 4: Generating complete system prompt...")
    system_prompt = prompt_builder.build_system_prompt()
    prompt_length = len(system_prompt)
    prompt_lines = system_prompt.count('\n') + 1
    print(f"  ✓ Generated system prompt: {prompt_length} characters, {prompt_lines} lines")
    print()
    
    # Step 5: Display prompt structure
    print("Step 5: System prompt structure:")
    sections = [
        "# EQL Query Generation Assistant",
        "## EQL Syntax Rules",
        "## EQL API Reference",
        "## EQL Query Examples",
        "## Available Entity Types and Schema",
        "## Output Format Requirements"
    ]
    
    for section in sections:
        if section in system_prompt:
            print(f"  ✓ {section}")
    print()
    
    # Step 6: Dump to file
    print("Step 6: Dumping system prompt to file...")
    output_dir = Path("examples/nlp_to_eql/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "eql_system_prompt.md"
    
    prompt_builder.dump_to_file(output_file)
    print(f"  ✓ System prompt saved to: {output_file}")
    print()
    
    # Step 7: Display sample from the prompt
    print("Step 7: Sample from generated system prompt:")
    print("-" * 80)
    
    # Show first few lines
    lines = system_prompt.split('\n')
    sample_lines = lines[:30]
    print('\n'.join(sample_lines))
    print("...")
    print("-" * 80)
    print()
    
    # Step 8: Show statistics
    print("Step 8: System Prompt Statistics:")
    print(f"  • Total characters: {prompt_length:,}")
    print(f"  • Total lines: {prompt_lines:,}")
    print(f"  • Available classes: {len(classes)}")
    print(f"  • Custom examples added: 3")
    print(f"  • Output file: {output_file}")
    print()
    
    print("=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Review the generated system prompt in:", output_file)
    print("  2. Use this prompt with LLM providers (OpenAI, Claude, Ollama)")
    print("  3. Convert natural language queries to EQL code")
    print()


if __name__ == "__main__":
    main()
