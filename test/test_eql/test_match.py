from ..dataset.semantic_world_like_classes import FixedConnection, Container, Handle
from krrood.entity_query_language.entity import the, entity_matching, match, entity, let
from krrood.entity_query_language.predicate import HasType


def test_match(handles_and_containers_world):
    world = handles_and_containers_world

    fixed_connection_query = the(
        entity_matching(FixedConnection, world.connections)(
            parent=match(Container)(name="Container1"),
            child=match(Handle)(name="Handle1"),
        )
    )

    fixed_connection_query_manual = the(
        entity(
            fc := let(FixedConnection, domain=None),
            HasType(fc.parent, Container),
            HasType(fc.child, Handle),
            fc.parent.name == "Container1",
            fc.child.name == "Handle1",
        )
    )

    assert fixed_connection_query == fixed_connection_query_manual

    fixed_connection_query.visualize()

    fixed_connection = fixed_connection_query.evaluate()
    assert isinstance(fixed_connection, FixedConnection)
    assert fixed_connection.parent.name == "Container1"
    assert isinstance(fixed_connection.child, Handle)
    assert fixed_connection.child.name == "Handle1"
