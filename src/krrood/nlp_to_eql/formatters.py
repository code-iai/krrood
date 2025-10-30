"""Formatters for converting ClassDiagram to LLM-friendly representations."""

from dataclasses import dataclass
from krrood.class_diagrams.class_diagram import ClassDiagram, WrappedClass, Association, Inheritance


@dataclass
class SchemaContextFormatter:
    """Formats ClassDiagram information into LLM-friendly schema descriptions."""
    
    class_diagram: ClassDiagram
    
    def format_for_prompt(self) -> str:
        """
        Format class diagram into a schema description for LLM prompts.
        
        :return: Formatted schema information as string
        """
        lines = []
        
        for wrapped_class in self.class_diagram.wrapped_classes:
            lines.append(self._format_class(wrapped_class))
        
        if self.class_diagram.associations:
            lines.append("\n### Relationships:")
            for association in self.class_diagram.associations:
                lines.append(self._format_association(association))
        
        if self.class_diagram.inheritance_relations:
            lines.append("\n### Inheritance:")
            for inheritance in self.class_diagram.inheritance_relations:
                lines.append(self._format_inheritance(inheritance))
        
        return "\n".join(lines)
    
    def _format_class(self, wrapped_class: WrappedClass) -> str:
        """
        Format a single class with its fields.
        
        :param wrapped_class: The wrapped class to format
        :return: Formatted class description
        """
        class_name = wrapped_class.clazz.__name__
        lines = [f"\n**{class_name}**:"]
        
        for wrapped_field in wrapped_class.fields:
            field_name = wrapped_field.public_name
            field_type = self._get_type_name(wrapped_field.type_endpoint)
            optional_marker = " (optional)" if wrapped_field.is_optional else ""
            container_marker = " (collection)" if wrapped_field.is_container else ""
            
            lines.append(f"  - {field_name}: {field_type}{optional_marker}{container_marker}")
        
        return "\n".join(lines)
    
    def _format_association(self, association: Association) -> str:
        """
        Format an association relationship.
        
        :param association: The association to format
        :return: Formatted association description
        """
        source_name = association.source.clazz.__name__
        target_name = association.target.clazz.__name__
        field_name = association.field.public_name
        
        return f"  - {source_name}.{field_name} → {target_name}"
    
    def _format_inheritance(self, inheritance: Inheritance) -> str:
        """
        Format an inheritance relationship.
        
        :param inheritance: The inheritance relationship to format
        :return: Formatted inheritance description
        """
        parent_name = inheritance.source.clazz.__name__
        child_name = inheritance.target.clazz.__name__
        
        return f"  - {child_name} inherits from {parent_name}"
    
    def _get_type_name(self, type_object) -> str:
        """
        Get readable type name.
        
        :param type_object: The type object
        :return: Human-readable type name
        """
        if hasattr(type_object, '__name__'):
            return type_object.__name__
        return str(type_object)
    
    def get_class_names(self) -> list[str]:
        """
        Get list of all class names in the diagram.
        
        :return: List of class names
        """
        return [wrapped_class.clazz.__name__ for wrapped_class in self.class_diagram.wrapped_classes]
    
    def get_classes_map(self) -> dict[str, type]:
        """
        Get mapping of class names to actual types.
        
        :return: Dictionary mapping class names to types
        """
        return {wrapped_class.clazz.__name__: wrapped_class.clazz 
                for wrapped_class in self.class_diagram.wrapped_classes}
    
    def format_as_pyi(self) -> str:
        """
        Format class diagram as Python stub file (.pyi) interface.
        
        :return: Python stub file content as string
        """
        lines = []
        
        # Add header
        lines.append('"""Type stubs for entity classes."""')
        lines.append("")
        lines.append("from dataclasses import dataclass")
        lines.append("from typing import Optional")
        lines.append("")
        
        # Build inheritance map
        inheritance_map = {}
        for inheritance in self.class_diagram.inheritance_relations:
            child_name = inheritance.target.clazz.__name__
            parent_name = inheritance.source.clazz.__name__
            inheritance_map[child_name] = parent_name
        
        # Format each class
        for wrapped_class in self.class_diagram.wrapped_classes:
            lines.append(self._format_class_as_pyi(wrapped_class, inheritance_map))
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_class_as_pyi(self, wrapped_class: WrappedClass, inheritance_map: dict) -> str:
        """
        Format a single class as Python stub syntax.
        
        :param wrapped_class: The wrapped class to format
        :param inheritance_map: Map of child class names to parent class names
        :return: Python stub class definition
        """
        class_name = wrapped_class.clazz.__name__
        lines = ["@dataclass"]
        
        # Add inheritance
        parent_name = inheritance_map.get(class_name)
        if parent_name:
            lines.append(f"class {class_name}({parent_name}):")
        else:
            lines.append(f"class {class_name}:")
        
        # Get only fields defined directly in this class, not inherited ones
        direct_fields = self._get_direct_fields(wrapped_class, parent_name)
        
        # Add fields
        if direct_fields:
            for wrapped_field in direct_fields:
                field_line = self._format_field_as_pyi(wrapped_field)
                lines.append(f"    {field_line}")
        else:
            lines.append("    pass")
        
        return "\n".join(lines)
    
    def _get_direct_fields(self, wrapped_class: WrappedClass, parent_name: str):
        """
        Get only fields defined directly in this class, excluding inherited fields.
        
        :param wrapped_class: The wrapped class
        :param parent_name: Name of parent class if any
        :return: List of fields defined directly in this class
        """
        if not parent_name:
            # No parent, all fields are direct
            return wrapped_class.fields
        
        # Get parent class fields
        parent_class = None
        for wc in self.class_diagram.wrapped_classes:
            if wc.clazz.__name__ == parent_name:
                parent_class = wc
                break
        
        if not parent_class:
            return wrapped_class.fields
        
        # Get parent field names
        parent_field_names = {wf.public_name for wf in parent_class.fields}
        
        # Return only fields not in parent
        return [wf for wf in wrapped_class.fields if wf.public_name not in parent_field_names]
    
    def _format_field_as_pyi(self, wrapped_field) -> str:
        """
        Format a single field as Python stub syntax.
        
        :param wrapped_field: The wrapped field to format
        :return: Python stub field definition
        """
        field_name = wrapped_field.public_name
        field_type = self._get_pyi_type_annotation(wrapped_field)
        
        return f"{field_name}: {field_type}"
    
    def _get_pyi_type_annotation(self, wrapped_field) -> str:
        """
        Get proper type annotation for a field in .pyi format.
        
        :param wrapped_field: The wrapped field
        :return: Type annotation string
        """
        type_name = self._get_type_name(wrapped_field.type_endpoint)
        
        if wrapped_field.is_container:
            container_type = wrapped_field.container_type.__name__ if wrapped_field.container_type else "list"
            type_annotation = f"{container_type}[{type_name}]"
        else:
            type_annotation = type_name
        
        if wrapped_field.is_optional:
            type_annotation = f"Optional[{type_annotation}]"
        
        return type_annotation
