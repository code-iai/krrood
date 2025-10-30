"""
Demo: RDF Generation with ORMatic

This example demonstrates how to generate both SQLAlchemy ORM models and RDF/OWL ontologies
from the same Python dataclasses using ORMatic.

The example creates a simple domain model for a robotics scenario with:
- Robot (has name, serial number, and optional location)
- Location (has x, y, z coordinates)
- Task (has description and assigned robot)
"""

from dataclasses import dataclass
from typing import Optional

from krrood.class_diagrams import ClassDiagram
from krrood.ormatic.ormatic import ORMatic


# Define domain classes
@dataclass
class Location:
    """Represents a 3D location."""
    x: float
    y: float
    z: float


@dataclass
class Robot:
    """Represents a robot with a name, serial number, and optional location."""
    name: str
    serial_number: str
    location: Optional[Location] = None


@dataclass
class Task:
    """Represents a task with a description and assigned robot."""
    description: str
    assigned_robot: Robot


def main():
    """Generate both SQL and RDF representations from the same model."""
    
    print("=" * 80)
    print("ORMatic RDF Generation Demo")
    print("=" * 80)
    print()
    
    # Step 1: Create a class diagram from our domain classes
    print("Step 1: Creating class diagram from domain classes...")
    diagram = ClassDiagram(classes=[Location, Robot, Task])
    print(f"  - Created diagram with {len(diagram.wrapped_classes)} classes")
    print()
    
    # Step 2: Create ORMatic instance
    print("Step 2: Creating ORMatic instance...")
    ormatic = ORMatic(class_dependency_graph=diagram)
    print(f"  - ORMatic initialized with {len(ormatic.wrapped_tables)} SQL tables")
    print(f"  - ORMatic initialized with {len(ormatic.wrapped_ontologies)} RDF ontologies")
    print()
    
    # Step 3: Generate SQLAlchemy ORM models
    print("Step 3: Generating SQLAlchemy ORM models...")
    with open("robot_sql_interface.py", "w") as f:
        ormatic.to_sqlalchemy_file(f)
    print("  - Generated: robot_sql_interface.py")
    print()
    
    # Step 4: Generate RDF/OWL ontology
    print("Step 4: Generating RDF/OWL ontology...")
    with open("robot_ontology.ttl", "w") as f:
        ormatic.to_rdf_file(f, namespace="http://example.org/robots#")
    print("  - Generated: robot_ontology.ttl")
    print()
    
    # Step 5: Display ontology statistics
    print("Step 5: Ontology Statistics")
    print("-" * 80)
    for wrapped_class, ontology in ormatic.wrapped_ontologies.items():
        print(f"\nClass: {ontology.class_name}")
        print(f"  Datatype Properties: {len(ontology.datatype_properties)}")
        for prop in ontology.datatype_properties:
            print(f"    - {prop.name}: {prop.range}")
        print(f"  Object Properties: {len(ontology.object_properties)}")
        for prop in ontology.object_properties:
            print(f"    - {prop.name} -> {prop.range}")
        if ontology.parent_classes:
            print(f"  Inherits from: {', '.join(ontology.parent_classes)}")
    print()
    
    # Step 6: Show a snippet of the generated RDF
    print("Step 6: Sample RDF Output (first 50 lines)")
    print("-" * 80)
    with open("robot_ontology.ttl", "r") as f:
        lines = f.readlines()[:50]
        for line in lines:
            print(line, end="")
    print()
    print("..." if len(lines) == 50 else "")
    print()
    
    print("=" * 80)
    print("Demo completed successfully!")
    print()
    print("Generated files:")
    print("  - robot_sql_interface.py  (SQLAlchemy ORM)")
    print("  - robot_ontology.ttl      (RDF/OWL Ontology in Turtle format)")
    print()
    print("Key takeaways:")
    print("  1. Single source of truth: Define your model once as Python dataclasses")
    print("  2. Multiple representations: Generate both SQL and RDF from the same model")
    print("  3. Type mapping: Primitive types -> xsd:datatype, Custom classes -> owl:ObjectProperty")
    print("  4. Inheritance: Python inheritance -> rdfs:subClassOf")
    print("=" * 80)


if __name__ == "__main__":
    main()
