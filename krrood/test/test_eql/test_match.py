import pytest

from krrood.entity_query_language.entity import (
    entity,
    let,
)
from krrood.entity_query_language.quantify_entity import an, the
from krrood.entity_query_language.match import (
    match,
    match_any,
    select,
    entity_matching,
    match_all,
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
    cabinet = an(entity_matching(Cabinet, cabinets)(drawers=match_any([my_drawer])))
    found_cabinets = list(cabinet.evaluate())
    assert len(found_cabinets) == 2
    assert cabinets[0] in found_cabinets
    assert cabinets[1] in found_cabinets


def test_match_all(world_and_cabinets_and_specific_drawer):
    world, cabinets, my_drawer = world_and_cabinets_and_specific_drawer
    cabinet = the(entity_matching(Cabinet, cabinets)(drawers=match_all([my_drawer])))
    found_cabinet = cabinet.evaluate()
    assert found_cabinet is cabinets[1]


def test_match_any_on_collection_returns_unique_parent_entities():
    # setup from the notebook example
    c1 = Container("Container1")
    other_c = Container("ContainerX")
    h1 = Handle("Handle1")

    drawer1 = Drawer(handle=h1, container=c1)
    drawer2 = Drawer(handle=Handle("OtherHandle"), container=other_c)
    cabinet1 = Cabinet(container=c1, drawers=[drawer1, drawer2])
    cabinet2 = Cabinet(container=other_c, drawers=[drawer2])
    views = [drawer1, drawer2, cabinet1, cabinet2]

    q = an(entity_matching(Cabinet, views)(drawers=match_any([drawer1, drawer2])))

    results = list(q.evaluate())
    # Expect exactly the two cabinets, no duplicates
    assert len(results) == 2
    assert {id(x) for x in results} == {id(cabinet1), id(cabinet2)}
