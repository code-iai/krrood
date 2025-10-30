"""
Tests for RDF generation from ORMatic models.
"""
import os.path
from io import StringIO
from pathlib import Path

import pytest

from krrood.class_diagrams import ClassDiagram
from krrood.ormatic.ormatic import ORMatic
from test.dataset.example_classes import (
    Position,
    Orientation,
    Pose,
    Position4D,
    Position5D,
    Positions,
    PositionsSubclassWithAnotherPosition,
    DoublePositionAggregator,
    Node,
    Atom,
    PhysicalObject,
    Cup,
    Bowl,
    OriginalSimulatedObject,
    ObjectAnnotation,
    KinematicChain,
    Torso,
    Parent,
    ChildMapped,
    ChildNotMapped,
    Entity,
    DerivedEntity,
    EntityAssociation,
    Reference,
    Backreference,
    AlternativeMappingAggregator,
    ItemWithBackreference,
    ContainerGeneration,
    Vector,
    Rotation,
    Transformation,
    Shape,
    Shapes,
    MoreShapes,
    VectorsWithProperty,
    ParentBase,
    ChildBase,
    PrivateDefaultFactory,
    RelationshipParent,
    RelationshipChild,
)


class TestRDFGeneration:
    """Test RDF generation from dataclasses."""

    def test_simple_class_to_rdf(self):
        """Test that a simple dataclass can be converted to RDF."""
        diagram = ClassDiagram(classes=[Position])
        ormatic = ORMatic(class_dependency_graph=diagram)

        output = StringIO()
        ormatic.to_rdf_file(output, namespace="http://example.org/ontology#")

        rdf_content = output.getvalue()

        # Check that the RDF contains expected elements
        assert "owl:Ontology" in rdf_content
        assert ":Position a owl:Class" in rdf_content
        assert "owl:DatatypeProperty" in rdf_content
        assert ":x" in rdf_content
        assert ":y" in rdf_content
        assert ":z" in rdf_content
        assert "xsd:float" in rdf_content

    def test_datatype_properties(self):
        """Test that primitive fields are converted to owl:DatatypeProperty."""
        diagram = ClassDiagram(classes=[Position])
        ormatic = ORMatic(class_dependency_graph=diagram)

        output = StringIO()
        ormatic.to_rdf_file(output, namespace="http://example.org/ontology#")

        rdf_content = output.getvalue()

        # Check for datatype properties
        assert ":x a owl:DatatypeProperty" in rdf_content
        assert ":y a owl:DatatypeProperty" in rdf_content
        assert ":z a owl:DatatypeProperty" in rdf_content
        assert "rdfs:domain :Position" in rdf_content
        assert "rdfs:range xsd:float" in rdf_content

    def test_object_properties(self):
        """Test that relationships are converted to owl:ObjectProperty."""
        diagram = ClassDiagram(classes=[Pose, Position, Orientation])
        ormatic = ORMatic(class_dependency_graph=diagram)

        output = StringIO()
        ormatic.to_rdf_file(output, namespace="http://example.org/ontology#")

        rdf_content = output.getvalue()

        # Check for object properties
        assert ":position a owl:ObjectProperty" in rdf_content
        assert ":orientation a owl:ObjectProperty" in rdf_content
        assert "rdfs:domain :Pose" in rdf_content
        assert "rdfs:range :Position" in rdf_content
        assert "rdfs:range :Orientation" in rdf_content

    def test_inheritance_to_subclassof(self):
        """Test that inheritance is converted to rdfs:subClassOf."""
        diagram = ClassDiagram(classes=[Position, Position4D, Position5D])
        ormatic = ORMatic(class_dependency_graph=diagram)

        output = StringIO()
        ormatic.to_rdf_file(output, namespace="http://example.org/ontology#")

        rdf_content = output.getvalue()

        # Check for inheritance relationships
        assert ":Position4D a owl:Class" in rdf_content
        assert ":Position5D a owl:Class" in rdf_content
        assert "rdfs:subClassOf :Position" in rdf_content
        assert "rdfs:subClassOf :Position4D" in rdf_content

    def test_optional_fields(self):
        """Test that optional fields are handled correctly."""
        diagram = ClassDiagram(classes=[Orientation])
        ormatic = ORMatic(class_dependency_graph=diagram)

        output = StringIO()
        ormatic.to_rdf_file(output, namespace="http://example.org/ontology#")

        rdf_content = output.getvalue()

        # Optional field w should still be present
        assert ":w a owl:DatatypeProperty" in rdf_content
        assert "rdfs:domain :Orientation" in rdf_content

    def test_list_fields(self):
        """Test that list fields are handled correctly."""
        diagram = ClassDiagram(classes=[Positions, Position])
        ormatic = ORMatic(class_dependency_graph=diagram)

        output = StringIO()
        ormatic.to_rdf_file(output, namespace="http://example.org/ontology#")

        rdf_content = output.getvalue()

        # List field positions should be an object property
        assert ":positions a owl:ObjectProperty" in rdf_content
        assert "rdfs:domain :Positions" in rdf_content
        assert "rdfs:range :Position" in rdf_content

        # List field some_strings should be a datatype property
        assert ":some_strings a owl:DatatypeProperty" in rdf_content
        assert "rdfs:range xsd:string" in rdf_content

    def test_self_referential_class(self):
        """Test that self-referential classes work correctly."""
        diagram = ClassDiagram(classes=[Node])
        ormatic = ORMatic(class_dependency_graph=diagram)

        output = StringIO()
        ormatic.to_rdf_file(output, namespace="http://example.org/ontology#")

        rdf_content = output.getvalue()

        # Node should have a parent property that references itself
        assert ":Node a owl:Class" in rdf_content
        assert ":parent a owl:ObjectProperty" in rdf_content
        assert "rdfs:domain :Node" in rdf_content
        assert "rdfs:range :Node" in rdf_content

    def test_multiple_classes(self):
        """Test that multiple classes are all included in the ontology."""
        diagram = ClassDiagram(classes=[Position, Orientation, Pose])
        ormatic = ORMatic(class_dependency_graph=diagram)

        output = StringIO()
        ormatic.to_rdf_file(output, namespace="http://example.org/ontology#")

        rdf_content = output.getvalue()

        # All classes should be present
        assert ":Position a owl:Class" in rdf_content
        assert ":Orientation a owl:Class" in rdf_content
        assert ":Pose a owl:Class" in rdf_content

    def test_namespace_in_output(self):
        """Test that the specified namespace appears in the output."""
        diagram = ClassDiagram(classes=[Position])
        ormatic = ORMatic(class_dependency_graph=diagram)

        namespace = "http://test.example.com/my-ontology#"
        output = StringIO()
        ormatic.to_rdf_file(output, namespace=namespace)

        rdf_content = output.getvalue()

        # Namespace should be in the output
        assert namespace in rdf_content
        assert f"<{namespace}> a owl:Ontology" in rdf_content

    def test_wrapped_ontologies_created(self):
        """Test that wrapped ontologies are created during initialization."""
        diagram = ClassDiagram(classes=[Position, Orientation])
        ormatic = ORMatic(class_dependency_graph=diagram)

        # Check that wrapped_ontologies dict is populated
        assert len(ormatic.wrapped_ontologies) == 2
        assert all(
            hasattr(ont, "datatype_properties")
            for ont in ormatic.wrapped_ontologies.values()
        )
        assert all(
            hasattr(ont, "object_properties")
            for ont in ormatic.wrapped_ontologies.values()
        )

    def test_rdf_structure(self):
        """Test that the generated RDF has proper structure."""
        diagram = ClassDiagram(classes=[Position])
        ormatic = ORMatic(class_dependency_graph=diagram)

        output = StringIO()
        ormatic.to_rdf_file(output, namespace="http://example.org/ontology#")

        rdf_content = output.getvalue()

        # Check for proper RDF prefixes
        assert "@prefix rdf:" in rdf_content
        assert "@prefix rdfs:" in rdf_content
        assert "@prefix owl:" in rdf_content
        assert "@prefix xsd:" in rdf_content

        # Check for sections
        assert "Classes" in rdf_content
        assert "Datatype Properties" in rdf_content

    def test_dump_all_dataset_classes_to_ttl(self, tmp_path):
        """Test that dumps all classes from test/dataset into a TTL file."""
        # Collect all Symbol-based classes from the dataset
        all_classes = [
            Position,
            Orientation,
            Pose,
            Position4D,
            Position5D,
            Positions,
            PositionsSubclassWithAnotherPosition,
            DoublePositionAggregator,
            Node,
            Atom,
            OriginalSimulatedObject,
            ObjectAnnotation,
            KinematicChain,
            Torso,
            Parent,
            ChildMapped,
            ChildNotMapped,
            Entity,
            DerivedEntity,
            EntityAssociation,
            Reference,
            Backreference,
            AlternativeMappingAggregator,
            ItemWithBackreference,
            ContainerGeneration,
            Vector,
            Rotation,
            Transformation,
            Shape,
            Shapes,
            MoreShapes,
            VectorsWithProperty,
            ParentBase,
            ChildBase,
            PrivateDefaultFactory,
            RelationshipParent,
            RelationshipChild,
        ]

        # Create class diagram from all classes
        diagram = ClassDiagram(classes=all_classes)
        ormatic = ORMatic(class_dependency_graph=diagram)

        # Generate TTL file
        output_file = tmp_path / "dataset_ontology.ttl"
        output_file = Path(os.path.join(os.path.dirname(__file__), "dataset_ontology.ttl"))
        with open(output_file, "w") as f:
            ormatic.to_rdf_file(f, namespace="http://test.dataset.org/ontology#")

        # Verify the file was created and contains valid content
        assert output_file.exists()
        content = output_file.read_text()

        # Verify it's valid Turtle RDF
        assert "@prefix rdf:" in content
        assert "@prefix owl:" in content
        assert "owl:Ontology" in content

        # Verify some classes are present
        assert ":Position a owl:Class" in content
        assert ":Pose a owl:Class" in content
        assert ":Entity a owl:Class" in content

        # Verify some properties are present
        assert "owl:DatatypeProperty" in content
        assert "owl:ObjectProperty" in content

        # Verify inheritance relationships
        assert "rdfs:subClassOf" in content

        # Print statistics
        num_classes = len([line for line in content.split("\n") if "a owl:Class" in line])
        num_datatype_props = len([line for line in content.split("\n") if "a owl:DatatypeProperty" in line])
        num_object_props = len([line for line in content.split("\n") if "a owl:ObjectProperty" in line])

        print(f"\nGenerated ontology statistics:")
        print(f"  Classes: {num_classes}")
        print(f"  Datatype Properties: {num_datatype_props}")
        print(f"  Object Properties: {num_object_props}")
        print(f"  File size: {len(content)} bytes")
        print(f"  Output file: {output_file}")
