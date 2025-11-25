import pytest

from krrood.entity_query_language.entity import (
    the,
    entity_matching,
    match,
    entity,
    let,
    select,
    an,
)
from krrood.entity_query_language.predicate import HasType
from krrood.entity_query_language.symbolic import UnificationDict, SetOf
from ..dataset.semantic_world_like_classes import (
    FixedConnection,
    Container,
    Handle,
    Cabinet,
    Drawer,
)


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


@pytest.fixture
def world_and_cabinets_and_specific_drawer(handles_and_containers_world):
    world = handles_and_containers_world
    my_drawer = Drawer(handle=Handle("Handle2"), container=Container("Container1"))
    drawers = list(filter(lambda v: isinstance(v, Drawer), world.views))
    my_cabinet_1 = Cabinet(
        container=Container("container2"), drawers=[my_drawer] + drawers
    )
    my_cabinet_2 = Cabinet(container=Container("container2"), drawers=[my_drawer])
    my_cabinet_3 = Cabinet(container=Container("container2"), drawers=drawers)
    return world, [my_cabinet_1, my_cabinet_2, my_cabinet_3], my_drawer


def test_match_any(world_and_cabinets_and_specific_drawer):
    world, cabinets, my_drawer = world_and_cabinets_and_specific_drawer
    cabinet = an(entity_matching(Cabinet, cabinets)(drawers=match([my_drawer]).any))
    found_cabinets = list(cabinet.evaluate())
    assert len(found_cabinets) == 2
    assert cabinets[0] in found_cabinets
    assert cabinets[1] in found_cabinets


def test_match_all(world_and_cabinets_and_specific_drawer):
    world, cabinets, my_drawer = world_and_cabinets_and_specific_drawer
    cabinet = the(entity_matching(Cabinet, cabinets)(drawers=[my_drawer]))
    found_cabinet = cabinet.evaluate()
    assert found_cabinet is cabinets[1]
