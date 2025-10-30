from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TextIO

import jinja2

if TYPE_CHECKING:
    from .ormatic import ORMatic

logger = logging.getLogger(__name__)


@dataclass
class RDFGenerator:
    """
    Generates RDF triples/ontologies from ORMatic models.
    Uses Jinja2 templates to generate RDF in Turtle format.
    """

    ormatic: ORMatic
    """The ORMatic instance that created this RDFGenerator."""

    namespace: str
    """Base URI for the ontology."""

    format: str = "turtle"
    """RDF serialization format (currently only turtle is supported)."""

    env: jinja2.Environment = field(init=False, default=None)
    """The environment to use with jinja2."""

    def __post_init__(self):
        """Initialize the Jinja2 environment."""
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def to_rdf_file(self, file: TextIO):
        """
        Generate RDF output from ORMatic models.
        
        :param file: The file to write to
        """
        # Ensure wrapped ontologies are created
        if not hasattr(self.ormatic, "wrapped_ontologies"):
            raise RuntimeError(
                "ORMatic instance does not have wrapped_ontologies. "
                "This might be because RDF support was not initialized."
            )

        # Load the template
        template = self.env.get_template("rdf_ontology.ttl.jinja")

        # Render the template
        output = template.render(
            ormatic=self.ormatic,
            namespace=self.namespace,
            ontologies=self.ormatic.wrapped_ontologies.values(),
        )

        # Write the output to the file
        file.write(output)
