from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Union, get_args, get_origin

from .rdf_types import get_xsd_type

if TYPE_CHECKING:
    from ..class_diagrams.class_diagram import WrappedClass
    from ..class_diagrams.wrapped_field import WrappedField
    from .ormatic import ORMatic

logger = logging.getLogger(__name__)


@dataclass
class RDFProperty:
    """
    Represents an RDF property definition (datatype or object property).
    """

    name: str
    """The name of the property."""

    property_type: str
    """Either 'owl:DatatypeProperty' or 'owl:ObjectProperty'."""

    domain: str
    """The domain class of the property."""

    range: str
    """The range (target type) of the property."""

    is_optional: bool = False
    """Whether the property is optional."""

    is_list: bool = False
    """Whether the property represents a list/collection."""

    def __str__(self) -> str:
        return f":{self.name} a {self.property_type}"


@dataclass
class WrappedOntology:
    """
    Wraps a dataclass and contains information for RDF representation.
    Similar to WrappedTable but for RDF/OWL ontologies.
    """

    wrapped_clazz: WrappedClass
    """The wrapped class that this ontology wraps."""

    ormatic: ORMatic
    """Reference to the ORMatic instance that created this WrappedOntology."""

    datatype_properties: List[RDFProperty] = field(default_factory=list, init=False)
    """List of owl:DatatypeProperty definitions for primitive fields."""

    object_properties: List[RDFProperty] = field(default_factory=list, init=False)
    """List of owl:ObjectProperty definitions for relationships."""

    def __post_init__(self):
        """Parse fields after initialization."""
        self.parse_fields()

    @property
    def class_name(self) -> str:
        """Get the class name for RDF representation."""
        return self.wrapped_clazz.clazz.__name__

    @property
    def parent_classes(self) -> List[str]:
        """Get the names of parent classes for rdfs:subClassOf relations."""
        parents = []
        for base in self.wrapped_clazz.clazz.__bases__:
            if base.__name__ not in ["Symbol", "object", "AlternativeMapping"]:
                parents.append(base.__name__)
        return parents

    def parse_fields(self):
        """Parse fields into RDF properties (object/datatype properties)."""
        for wrapped_field in self.wrapped_clazz.fields:
            if self._should_skip_field(wrapped_field):
                continue

            if self._is_object_property(wrapped_field):
                self._create_object_property(wrapped_field)
            else:
                self._create_datatype_property(wrapped_field)

    def _should_skip_field(self, wrapped_field: WrappedField) -> bool:
        """
        Determine if a field should be skipped.
        Mirrors the logic in WrappedTable.parse_fields to maintain consistency.
        
        :param wrapped_field: The field to check
        :return: True if the field should be skipped
        """
        # Skip internal fields like database_id
        if wrapped_field.field.name == "database_id":
            return True
        
        # Skip private fields (starting with _)
        if wrapped_field.field.name.startswith("_"):
            return True
        
        # Only process fields that match the types handled in SQL generation
        # Based on WrappedTable.parse_field logic
        is_handled = (
            wrapped_field.is_type_type
            or (
                (wrapped_field.is_builtin_type or wrapped_field.is_enum)
                and not wrapped_field.is_container
            )
            or (
                wrapped_field.is_one_to_one_relationship
                and wrapped_field.type_endpoint in self.ormatic.mapped_classes
            )
            or (
                wrapped_field.is_one_to_one_relationship
                and wrapped_field.type_endpoint in self.ormatic.type_mappings
            )
            or wrapped_field.is_collection_of_builtins
            or wrapped_field.is_one_to_many_relationship
        )
        
        return not is_handled

    def _extract_inner_type(self, field_type: str) -> str:
        """
        Extract the inner type from Optional, List, etc. string annotations.
        
        :param field_type: The type string to parse
        :return: The inner type name
        """
        # Handle Optional[X] -> X
        if field_type.startswith("Optional[") and field_type.endswith("]"):
            return field_type[9:-1]
        
        # Handle List[X] -> X
        if field_type.startswith("List[") and field_type.endswith("]"):
            return field_type[5:-1]
        
        return field_type

    def _is_object_property(self, wrapped_field: WrappedField) -> bool:
        """
        Determine if a field should be an owl:ObjectProperty.
        
        :param wrapped_field: The field to check
        :return: True if it's an object property (relationship)
        """
        field_type = wrapped_field.field.type

        # Handle Optional types
        if get_origin(field_type) is Union:
            args = get_args(field_type)
            if args:
                field_type = args[0]

        # Handle List types
        if get_origin(field_type) is list:
            args = get_args(field_type)
            if args:
                field_type = args[0]

        # Handle string type annotations (from __future__ import annotations)
        if isinstance(field_type, str):
            # Extract inner type from Optional/List wrappers
            field_type = self._extract_inner_type(field_type)
            
            # It's an object property if it's not a builtin type name
            builtin_types = {"int", "float", "str", "bool", "bytes", "bytearray", 
                           "complex", "dict", "frozenset", "list", "set", "tuple",
                           "None", "type"}
            if field_type not in builtin_types:
                return True
            return False

        # Check if it's a custom class (not a builtin type)
        if isinstance(field_type, type):
            # It's an object property if it's not a builtin type and not an Enum
            if field_type.__module__ not in ["builtins", "typing"] and not issubclass(
                field_type, Enum
            ):
                return True

        return False

    def _create_datatype_property(self, wrapped_field: WrappedField):
        """
        Create owl:DatatypeProperty for primitive types.
        
        :param wrapped_field: The field to create a property for
        """
        field_type = wrapped_field.field.type
        is_optional = False
        is_list = False

        # Handle Optional types
        if get_origin(field_type) is Union:
            is_optional = True
            args = get_args(field_type)
            if args:
                field_type = args[0]

        # Handle List types
        if get_origin(field_type) is list:
            is_list = True
            args = get_args(field_type)
            if args:
                field_type = args[0]

        # Handle string type annotations
        if isinstance(field_type, str):
            # Check for Optional/List wrappers
            original_type = field_type
            field_type = self._extract_inner_type(field_type)
            
            if original_type.startswith("Optional["):
                is_optional = True
            if original_type.startswith("List["):
                is_list = True

        # Get XSD type
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            xsd_type = "xsd:string"  # Enums as strings
        else:
            xsd_type = get_xsd_type(field_type)

        prop = RDFProperty(
            name=wrapped_field.field.name,
            property_type="owl:DatatypeProperty",
            domain=self.class_name,
            range=xsd_type,
            is_optional=is_optional,
            is_list=is_list,
        )
        self.datatype_properties.append(prop)

    def _create_object_property(self, wrapped_field: WrappedField):
        """
        Create owl:ObjectProperty for relationships.
        
        :param wrapped_field: The field to create a property for
        """
        field_type = wrapped_field.field.type
        is_optional = False
        is_list = False

        # Handle Optional types
        if get_origin(field_type) is Union:
            is_optional = True
            args = get_args(field_type)
            if args:
                field_type = args[0]

        # Handle List types
        if get_origin(field_type) is list:
            is_list = True
            args = get_args(field_type)
            if args:
                field_type = args[0]

        # Handle string type annotations
        if isinstance(field_type, str):
            # Check for Optional/List wrappers
            original_type = field_type
            field_type = self._extract_inner_type(field_type)
            
            if original_type.startswith("Optional["):
                is_optional = True
            if original_type.startswith("List["):
                is_list = True

        # Get the class name of the target
        if isinstance(field_type, type):
            target_class_name = field_type.__name__
        else:
            target_class_name = str(field_type)

        prop = RDFProperty(
            name=wrapped_field.field.name,
            property_type="owl:ObjectProperty",
            domain=self.class_name,
            range=target_class_name,
            is_optional=is_optional,
            is_list=is_list,
        )
        self.object_properties.append(prop)

    @property
    def all_properties(self) -> List[RDFProperty]:
        """Get all properties (datatype and object) for this class."""
        return self.datatype_properties + self.object_properties
