import operator

from krrood.entity_query_language.symbolic import UnificationDict, SetOf
from ..dataset.semantic_world_like_classes import (
    FixedConnection,
    Container,
    Handle,
    Cabinet,
    Drawer,
)
from krrood.entity_query_language.entity import (
    the,
    entity_matching,
    match,
    entity,
    let,
    select,
    match_any,
    a,
    an,
)
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


def test_select(handles_and_containers_world):
    world = handles_and_containers_world
    container, handle = select(Container), select(Handle)
    fixed_connection_query = the(
        entity_matching(FixedConnection, world.connections)(
            parent=container(name="Container1"),
            child=handle(name="Handle1"),
        )
    )

    assert isinstance(fixed_connection_query._child_, SetOf)

    answers = fixed_connection_query.evaluate()
    assert isinstance(answers, UnificationDict)
    assert answers[container].name == "Container1"
    assert answers[handle].name == "Handle1"


def test_match_any(handles_and_containers_world):
    world = handles_and_containers_world
    drawer = the(
        entity_matching(Drawer, world.views)(handle=match(Handle)(name="Handle1"))
    )
    cabinet = the(entity_matching(Cabinet, world.views)(drawers=match_any(drawer)))
    found_cabinet = cabinet.evaluate()
    assert found_cabinet.drawers[0].handle.name == "Handle1"
    assert cabinet._child_._child_.operation is operator.contains
    assert cabinet._child_._child_.right is drawer
