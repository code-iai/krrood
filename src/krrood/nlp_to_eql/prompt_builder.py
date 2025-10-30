"""System prompt builder for Natural Language to EQL conversion."""

from dataclasses import dataclass, field
from pathlib import Path
from .models import EQLExample
from .formatters import SchemaContextFormatter
from krrood.class_diagrams.class_diagram import ClassDiagram


@dataclass
class SystemPromptBuilder:
    """
    Builds comprehensive system prompts for LLM-based natural language to EQL conversion.
    Includes EQL syntax rules, API examples, and schema context.
    """
    
    class_diagram: ClassDiagram
    examples: list[EQLExample] = field(default_factory=list)
    
    def build_system_prompt(self) -> str:
        """
        Build complete system prompt with EQL syntax, examples, and schema.
        
        :return: Complete system prompt string
        """
        sections = [
            self._build_header(),
            self._build_eql_syntax_section(),
            self._build_eql_api_section(),
            self._build_examples_section(),
            self._build_schema_section(),
            self._build_pyi_interface_section(),
            self._build_output_format_section(),
        ]
        
        return "\n\n".join(sections)
    
    def dump_to_file(self, file_path: str | Path):
        """
        Dump the complete system prompt to a file.
        
        :param file_path: Path where the system prompt will be saved
        """
        prompt = self.build_system_prompt()
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            f.write(prompt)
    
    def _build_header(self) -> str:
        """Build system prompt header."""
        return """# EQL Query Generation Assistant

You are an expert in converting natural language descriptions to EQL (Entity Query Language) queries.
EQL is a pythonic, relational query language that provides implicit joins through relationship expressions.

Your role is to help users write correct EQL queries by understanding their natural language descriptions
and generating syntactically correct, executable EQL code."""
    
    def _build_eql_syntax_section(self) -> str:
        """Build EQL syntax rules section."""
        return """## EQL Syntax Rules

### Core Constructs

**Variable Declaration:**
```python
let(Type, domain=collection, name="optional_name")
```
- Declares a symbolic variable of a specific type
- `domain` specifies the collection to search within
- `name` is optional but helps with readability

**Single Entity Selection:**
```python
entity(variable, *conditions)
```
- Selects a single variable from the query
- Conditions filter which instances match

**Multiple Entity Selection:**
```python
set_of((var1, var2, ...), *conditions)
```
- Returns tuples of multiple variables
- Useful for queries involving multiple related entities

**Quantifiers:**
```python
an(...)  # Returns generator for multiple results
the(...) # Returns single result, raises error if multiple matches
```

### Logical Operators

```python
and_(*conditions)      # Logical AND
or_(*conditions)       # Logical OR
not_(condition)        # Logical NOT
```

### Comparison Operators

```python
variable.field == value          # Equality
variable.field > value           # Greater than
variable.field < value           # Less than
variable.field >= value          # Greater than or equal
variable.field <= value          # Less than or equal
in_(value, collection)           # Membership test
contains(collection, value)      # Collection contains value
```

### String Methods

Python string methods work on symbolic string attributes:
```python
variable.name.startswith("prefix")
variable.name.endswith("suffix")
variable.name.lower()
variable.name.upper()
```

### Relationships and Implicit Joins

Express relationships through equality between entity attributes:
```python
connection.parent == body        # Join condition
child.parent_id == parent.id     # Foreign key relationship
```

### Context Manager

All EQL queries must be wrapped in `symbolic_mode()`:
```python
with symbolic_mode():
    query = an(entity(var := let(Type, domain=data), conditions))
```"""
    
    def _build_eql_api_section(self) -> str:
        """Build EQL API reference section."""
        return """## EQL API Reference

### Required Imports

```python
from krrood.entity_query_language.entity import (
    let, entity, set_of, an, the,
    and_, or_, not_, in_, contains
)
from krrood.entity_query_language.symbolic import symbolic_mode
```

### Key Functions and Classes

**`let(type_, domain, name=None)`**
- `type_`: The class/type of entity to declare
- `domain`: Collection to search (list, set, etc.)
- `name`: Optional identifier for debugging
- Returns: Symbolic variable representing an entity

**`entity(variable, *conditions)`**
- `variable`: The symbolic variable to return
- `*conditions`: Zero or more conditions that must be satisfied
- Returns: Query specification for a single entity

**`set_of(variables, *conditions)`**
- `variables`: Tuple of symbolic variables to return
- `*conditions`: Conditions that bind the variables
- Returns: Query specification for multiple entities

**`an(query_spec)`**
- `query_spec`: Result of `entity()` or `set_of()`
- Returns: Generator that yields all matching results
- Use: `.evaluate()` to get results as a list

**`the(query_spec)`**
- `query_spec`: Result of `entity()` or `set_of()`
- Returns: Single result or raises error
- Use: `.evaluate()` to get the unique result

**`and_(*conditions)`**
- Combines multiple conditions with logical AND
- All conditions must be true

**`or_(*conditions)`**
- Combines multiple conditions with logical OR
- At least one condition must be true

**`not_(condition)`**
- Negates a condition

**`in_(value, collection)`**
- Checks if value is in collection
- Alternative to `contains(collection, value)`

**`contains(collection, value)`**
- Checks if collection contains value
- Alternative to `in_(value, collection)`"""
    
    def _build_examples_section(self) -> str:
        """Build examples section from stored examples."""
        if not self.examples:
            return self._build_default_examples()
        
        lines = ["## EQL Query Examples"]
        
        # Group examples by category
        categories = {}
        for example in self.examples:
            if example.category not in categories:
                categories[example.category] = []
            categories[example.category].append(example)
        
        for category, examples in categories.items():
            lines.append(f"\n### {category.replace('_', ' ').title()}")
            for example in examples:
                lines.append(f"\n**{example.description}**")
                if example.natural_language:
                    lines.append(f"Natural Language: \"{example.natural_language}\"")
                lines.append(f"```python\n{example.eql_code}\n```")
        
        return "\n".join(lines)
    
    def _build_default_examples(self) -> str:
        """Build default examples section."""
        return """## EQL Query Examples

### Basic Filtering

**Simple equality filter:**
Natural Language: "Find bodies with name equal to 'Body1'"
```python
with symbolic_mode():
    body = let(Body, domain=world.bodies)
    query = an(entity(body, body.name == "Body1"))
results = query.evaluate()
```

**Comparison operators:**
Natural Language: "Find positions where z is greater than 3"
```python
with symbolic_mode():
    position = let(Position, domain=positions)
    query = an(entity(position, position.z > 3))
results = query.evaluate()
```

### String Operations

**String prefix matching:**
Natural Language: "Find bodies whose name starts with 'Container'"
```python
with symbolic_mode():
    body = let(Body, domain=world.bodies)
    query = an(entity(body, body.name.startswith("Container")))
results = query.evaluate()
```

**String suffix matching:**
Natural Language: "Find bodies whose name ends with '2'"
```python
with symbolic_mode():
    body = let(Body, domain=world.bodies)
    query = an(entity(body, body.name.endswith("2")))
results = query.evaluate()
```

**Combined string conditions:**
Natural Language: "Find bodies whose name starts with 'Body' and ends with '2'"
```python
with symbolic_mode():
    body = let(Body, domain=world.bodies)
    query = an(entity(body, and_(
        body.name.startswith("Body"),
        body.name.endswith("2")
    )))
results = query.evaluate()
```

### Membership Testing

**Using in_ operator:**
Natural Language: "Find bodies whose name is in the list ['Container1', 'Handle1']"
```python
with symbolic_mode():
    body = let(Body, domain=world.bodies)
    query = an(entity(body, in_(body.name, ["Container1", "Handle1"])))
results = query.evaluate()
```

**Using contains operator:**
```python
with symbolic_mode():
    body = let(Body, domain=world.bodies)
    names = ["Container1", "Handle1"]
    query = an(entity(body, contains(names, body.name)))
results = query.evaluate()
```

### Logical Combinations

**OR condition:**
Natural Language: "Find positions where z equals 4 or x equals 2"
```python
with symbolic_mode():
    position = let(Position, domain=positions)
    query = an(entity(position, or_(
        position.z == 4,
        position.x == 2
    )))
results = query.evaluate()
```

**AND condition:**
Natural Language: "Find bodies where name starts with 'Container' and ends with '1'"
```python
with symbolic_mode():
    body = let(Body, domain=world.bodies)
    query = an(entity(body, and_(
        body.name.startswith("Container"),
        body.name.endswith("1")
    )))
results = query.evaluate()
```

**NOT condition:**
Natural Language: "Find bodies whose name does not start with 'Handle'"
```python
with symbolic_mode():
    body = let(Body, domain=world.bodies)
    query = an(entity(body, not_(body.name.startswith("Handle"))))
results = query.evaluate()
```

### Relationship Queries (Implicit Joins)

**One-to-one relationship:**
Natural Language: "Find poses where the position's z coordinate is greater than 3"
```python
with symbolic_mode():
    pose = let(Pose, domain=poses)
    query = an(entity(pose, pose.position.z > 3))
results = query.evaluate()
```

**Entity equality (join condition):**
Natural Language: "Find fixed connections where the parent is a specific body"
```python
with symbolic_mode():
    body = let(Body, domain=world.bodies)
    connection = let(FixedConnection, domain=world.connections)
    query = an(entity(connection, connection.parent == body))
results = query.evaluate()
```

**Multi-entity relationships:**
Natural Language: "Find prismatic and fixed connections where the child of prismatic equals the parent of fixed"
```python
with symbolic_mode():
    prismatic = let(PrismaticConnection, domain=world.connections)
    fixed = let(FixedConnection, domain=world.connections)
    query = an(entity(fixed, fixed.parent == prismatic.child))
results = query.evaluate()
```

### Multiple Entity Selection

**Selecting multiple related entities:**
Natural Language: "Find all combinations of parent container, prismatic connection, drawer, fixed connection, and handle"
```python
with symbolic_mode():
    parent = let(Body, domain=world.bodies)
    prismatic = let(PrismaticConnection, domain=world.connections)
    drawer = let(Body, domain=world.bodies)
    fixed = let(FixedConnection, domain=world.connections)
    handle = let(Body, domain=world.bodies)
    
    query = an(set_of(
        (parent, prismatic, drawer, fixed, handle),
        and_(
            parent == prismatic.parent,
            drawer == prismatic.child,
            drawer == fixed.parent,
            handle == fixed.child
        )
    ))
results = query.evaluate()
```

### Unique Result Queries

**Using 'the' quantifier:**
Natural Language: "Find the unique position where y equals 5"
```python
with symbolic_mode():
    position = let(Position, domain=positions)
    query = the(entity(position, position.y == 5))
result = query.evaluate()  # Raises error if multiple or no results
```"""
    
    def _build_schema_section(self) -> str:
        """Build schema context section from ClassDiagram."""
        formatter = SchemaContextFormatter(self.class_diagram)
        schema_info = formatter.format_for_prompt()
        class_names = ", ".join(formatter.get_class_names())
        
        return f"""## Available Entity Types and Schema

The following entity types are available for queries:
**Classes:** {class_names}

{schema_info}"""
    
    def _build_pyi_interface_section(self) -> str:
        """Build Python stub interface section from ClassDiagram."""
        formatter = SchemaContextFormatter(self.class_diagram)
        pyi_content = formatter.format_as_pyi()
        
        return f"""## Python Type Interface (.pyi)

The following shows the complete type interface for all available entity classes.
Use this to understand the exact types, fields, and relationships:

```python
{pyi_content}
```"""
    
    def _build_output_format_section(self) -> str:
        """Build output format guidelines."""
        return """## Output Format Requirements

When generating EQL queries, follow these rules:

1. **Always use symbolic_mode context manager:**
   ```python
   with symbolic_mode():
       # Your query here
   ```

2. **Use walrus operator for variable assignment in queries:**
   ```python
   query = an(entity(body := let(Body, domain=data), conditions))
   ```

3. **Include necessary imports:**
   ```python
   from krrood.entity_query_language.entity import let, entity, an, the, and_, or_, not_, in_, contains
   from krrood.entity_query_language.symbolic import symbolic_mode
   ```

4. **Return complete, executable code:**
   - Include the context manager
   - Include the query definition
   - Optionally include `.evaluate()` call

5. **Use meaningful variable names:**
   - Use descriptive names that match the domain (e.g., `body`, `connection`, `position`)
   - Avoid single letters unless in simple examples

6. **Handle multiple conditions properly:**
   - Use `and_()`, `or_()`, `not_()` for combining conditions
   - Don't use Python's `and`, `or`, `not` keywords directly

7. **Use appropriate quantifiers:**
   - Use `an()` when expecting multiple results
   - Use `the()` when expecting exactly one result"""

    def add_example(self, description: str, natural_language: str, 
                   eql_code: str, category: str = "general"):
        """
        Add a custom EQL example to the system prompt.
        
        :param description: Brief description of what the query does
        :param natural_language: Natural language version of the query
        :param eql_code: The actual EQL code
        :param category: Category for grouping (e.g., "filtering", "joins")
        """
        self.examples.append(EQLExample(
            description=description,
            natural_language=natural_language,
            eql_code=eql_code,
            category=category
        ))
