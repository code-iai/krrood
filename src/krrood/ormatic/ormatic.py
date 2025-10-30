from __future__ import annotations

import logging
from dataclasses import dataclass, field

import rustworkx as rx
from sortedcontainers import SortedSet
from sqlalchemy import TypeDecorator
from typing_extensions import List, Type, Dict
from typing_extensions import Optional, TextIO

from .custom_types import TypeType
from .dao import AlternativeMapping
from .rdf_generator import RDFGenerator
from .sqlalchemy_generator import SQLAlchemyGenerator
from .utils import InheritanceStrategy, module_and_class_name
from .wrapped_ontology import WrappedOntology
from .wrapped_table import WrappedTable
from ..class_diagrams.class_diagram import (
    ClassDiagram,
    ClassRelation,
    WrappedClass,
)
from ..class_diagrams.wrapped_field import WrappedField

logger = logging.getLogger(__name__)


class AlternativelyMaps(ClassRelation):
    """
    Edge type that says that the source alternativly maps the target, e. g.
    `AlternativeMaps(source=PointMapping, target=Point)` means that PointMapping is the mapping for Point.
    """


@dataclass
class ORMatic:
    """
    ORMatic is a tool for generating SQLAlchemy ORM models from a set of dataclasses.
    """

    class_dependency_graph: ClassDiagram
    """
    The class diagram to add the orm for.
    """

    alternative_mappings: List[Type[AlternativeMapping]] = field(default_factory=list)
    """
    List of alternative mappings that should be used to map classes.
    """

    type_mappings: Dict[Type, Type[TypeDecorator]] = field(default_factory=dict)
    """
    A dict that maps classes to custom types that should be used to save the classes.
    They keys of the type mappings must be disjoint with the classes given..
    """

    inheritance_strategy: InheritanceStrategy = InheritanceStrategy.JOINED
    """
    The inheritance strategy to use.
    """

    foreign_key_postfix = "_id"
    """
    The postfix that will be added to foreign key columns (not the relationships).
    """

    imported_modules: SortedSet[str] = field(default_factory=SortedSet, init=False)
    """
    A set of modules that need to be imported.
    """

    type_annotation_map: Dict[str, str] = field(default_factory=dict, init=False)
    """
    The string version of type mappings that is used in jinja.
    """

    inheritance_graph: rx.PyDiGraph[int] = field(default=None, init=False)
    """
    A graph that represents the inheritance structure of the classes. Extracted from the class dependency graph.
    """

    wrapped_tables: Dict[WrappedClass, WrappedTable] = field(
        default_factory=dict, init=False
    )
    """
    The wrapped tables instances for the SQLAlchemy conversion.
    """

    wrapped_ontologies: Dict[WrappedClass, WrappedOntology] = field(
        default_factory=dict, init=False
    )
    """
    The wrapped ontologies instances for RDF conversion.
    """

    def __post_init__(self):
        self.type_mappings[Type] = TypeType
        self.imported_modules.add(Type.__module__)
        self._create_inheritance_graph()
        self._add_alternative_mappings_to_class_diagram()
        self._create_wrapped_tables()
        self._create_wrapped_ontologies()

        for wrapped_table in self.wrapped_tables.values():
            self.imported_modules.add(wrapped_table.wrapped_clazz.clazz.__module__)

    def _create_wrapped_tables(self):
        for wrapped_clazz in self.wrapped_classes_in_topological_order:

            # check if the class has an alternative mapping
            if alternative_mapping := self.get_alternative_mapping(wrapped_clazz):
                # add the alternative mapping
                self.wrapped_tables[wrapped_clazz] = WrappedTable(
                    wrapped_clazz=alternative_mapping, ormatic=self
                )
            else:
                # add the class normally
                self.wrapped_tables[wrapped_clazz] = WrappedTable(
                    wrapped_clazz=wrapped_clazz, ormatic=self
                )

    def _create_wrapped_ontologies(self):
        """
        Create wrapped ontologies for RDF generation.
        """
        for wrapped_clazz in self.wrapped_classes_in_topological_order:
            # check if the class has an alternative mapping
            if alternative_mapping := self.get_alternative_mapping(wrapped_clazz):
                # add the alternative mapping
                self.wrapped_ontologies[wrapped_clazz] = WrappedOntology(
                    wrapped_clazz=alternative_mapping, ormatic=self
                )
            else:
                # add the class normally
                self.wrapped_ontologies[wrapped_clazz] = WrappedOntology(
                    wrapped_clazz=wrapped_clazz, ormatic=self
                )

    def _create_inheritance_graph(self):
        self.inheritance_graph = rx.PyDiGraph()
        self.inheritance_graph.add_nodes_from(
            [w.index for w in self.class_dependency_graph.wrapped_classes]
        )
        for edge in self.class_dependency_graph.inheritance_relations:
            self.inheritance_graph.add_edge(edge.source.index, edge.target.index, None)

    def _add_alternative_mappings_to_class_diagram(self):
        """
        Add alternative mappings to the class diagram.
        """
        for alternative_mapping in self.alternative_mappings:
            wrapped_alternative_mapping = WrappedClass(clazz=alternative_mapping)
            self.class_dependency_graph.add_node(wrapped_alternative_mapping)
            self.class_dependency_graph.add_relation(
                AlternativelyMaps(
                    source=wrapped_alternative_mapping,
                    target=self.class_dependency_graph.get_wrapped_class(
                        alternative_mapping.original_class()
                    ),
                )
            )

    @property
    def alternatively_maps_relations(self) -> List[AlternativelyMaps]:
        return [
            edge
            for edge in self.class_dependency_graph._dependency_graph.edges()
            if isinstance(edge, AlternativelyMaps)
        ]

    def get_alternative_mapping(
        self, wrapped_class: WrappedClass
    ) -> Optional[WrappedClass]:
        """
        Finds and returns an alternative mapping for the given wrapped class,
        if one exists, based on the relations specified in
        `alternatively_maps_relations`.

        :param wrapped_class: The wrapped class for which an alternative
            mapping is to be searched.
        :return: An alternate mapping of the type WrappedClass if found,
            otherwise None.
        """
        for rel in self.alternatively_maps_relations:
            if rel.target == wrapped_class:
                return rel.source
        return None

    def create_type_annotations_map(self):
        self.type_annotation_map = {"Type": "TypeType"}
        for clazz, custom_type in self.type_mappings.items():
            self.type_annotation_map[module_and_class_name(clazz)] = (
                module_and_class_name(custom_type)
            )

    @property
    def wrapped_classes_in_topological_order(self) -> List[WrappedClass]:
        """
        :return: List of all tables in topological order.
        """
        return [
            self.class_dependency_graph._dependency_graph[index]
            for index in rx.topological_sort(self.inheritance_graph)
        ]

    @property
    def mapped_classes(self) -> List[Type]:
        return [key.clazz for key in self.wrapped_tables.keys()]

    def make_all_tables(self):
        for table in self.wrapped_tables.values():
            table.parse_fields()

    def foreign_key_name(self, wrapped_field: WrappedField) -> str:
        """
        :return: A foreign key name for the given field.
        """
        return f"{wrapped_field.clazz.clazz.__name__.lower()}_{wrapped_field.field.name}{self.foreign_key_postfix}"

    def to_sqlalchemy_file(self, file: TextIO):
        """
        Generate a Python file with SQLAlchemy declarative mappings from the ORMatic models.

        :param file: The file to write to
        """
        sqlalchemy_generator = SQLAlchemyGenerator(self)
        sqlalchemy_generator.to_sqlalchemy_file(file)

    def to_rdf_file(self, file: TextIO, namespace: str, format: str = "turtle"):
        """
        Generate RDF ontology from the ORMatic models.

        :param file: The file to write to
        :param namespace: Base URI for the ontology
        :param format: RDF serialization format (turtle, rdf/xml, n3, etc.)
        """
        rdf_generator = RDFGenerator(self, namespace=namespace, format=format)
        rdf_generator.to_rdf_file(file)
