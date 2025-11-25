---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Pattern matching with `match` and `entity_matching`

EQL provides a concise pattern-matching API for building nested structural queries.
Use `match(type_)(...)` to describe a nested pattern on attributes, and wrap the outermost match
with `entity_matching(type_, domain)(...)` when you also need to bind a search domain.

The following example shows how nested patterns translate
into an equivalent manual query built with `entity(...)` and predicates.

```{code-cell} ipython3
from dataclasses import dataclass
from typing_extensions import List

from krrood.entity_query_language.entity import (
    let, entity, Symbol,
)
from krrood.entity_query_language.quantify_entity import the
from krrood.entity_query_language.match import (
    match,
    entity_matching,
)
from krrood.entity_query_language.predicate import HasType


# --- Model -------------------------------------------------------------
@dataclass
class Body(Symbol):
    name: str


@dataclass
class Handle(Body):
    ...


@dataclass
class Container(Body):
    ...


@dataclass
class Connection(Symbol):
    parent: Body
    child: Body


@dataclass
class FixedConnection(Connection):
    ...


@dataclass
class World:
    connections: List[Connection]


# Build a small world with a few connections
c1 = Container("Container1")
h1 = Handle("Handle1")
other_c = Container("ContainerX")
other_h = Handle("HandleY")

world = World(
    connections=[
        FixedConnection(parent=c1, child=h1),
        FixedConnection(parent=other_c, child=h1),
    ]
)
```

## Matching a nested structure

`entity_matching(FixedConnection, world.connections)` selects from `world.connections` items of type
`FixedConnection`. Inner `match(...)` clauses describe constraints on attributes of that selected item.

```{code-cell} ipython3
fixed_connection_query = the(
    entity_matching(FixedConnection, world.connections)(
        parent=match(Container)(name="Container1"),
        child=match(Handle)(name="Handle1"),
    )
)
```

## The equivalent manual query

You can express the same query explicitly using `entity`, `let`, attribute comparisons, and `HasType` for
attribute type constraints:

```{code-cell} ipython3
fc = let(FixedConnection, domain=None)
fixed_connection_query_manual = the(
    entity(
        fc,
        HasType(fc.parent, Container),
        HasType(fc.child, Handle),
        fc.parent.name == "Container1",
        fc.child.name == "Handle1",
    )
)

# The two query objects are structurally equivalent
assert fixed_connection_query == fixed_connection_query_manual
```

## Evaluate the query

```{code-cell} ipython3
fixed_connection = fixed_connection_query.evaluate()
print(type(fixed_connection).__name__, fixed_connection.parent.name, fixed_connection.child.name)
```

Notes:
- Use `entity_matching` for the outer pattern when a domain is involved; inner attributes use `match`.
- Nested `match(...)` can be composed arbitrarily deep following your object graph.
- `entity_matching` is a syntactic sugar over the explicit `entity` + predicates form, so both are interchangeable.

## Selecting inner objects with `select()`

Use `select(Type)` when you want the matched inner objects to appear in the result. The evaluation then
returns a mapping from the selected variables to the concrete objects (a unification dictionary).

```{code-cell} ipython3
from krrood.entity_query_language.match import select

container, handle = select(Container), select(Handle)
fixed_connection_query = the(
    entity_matching(FixedConnection, world.connections)(
        parent=container(name="Container1"),
        child=handle(name="Handle1"),
    )
)

answers = fixed_connection_query.evaluate()
print(answers[container].name, answers[handle].name)
```

## Existential matches in collections with `match_any()`

When matching a container-like attribute (for example, a list), use `match_any(pattern)` to express that
at least one element of the collection should satisfy the given pattern.

Below we add two simple view classes and build a small scene of drawers and a cabinet.

```{code-cell} ipython3
from dataclasses import dataclass
from typing_extensions import List
from krrood.entity_query_language.match import match_any


@dataclass
class Drawer(Symbol):
    handle: Handle
    container: Container


@dataclass
class Cabinet(Symbol):
    container: Container
    drawers: List[Drawer]


# Build a simple set of views
drawer1 = Drawer(handle=h1, container=c1)
drawer2 = Drawer(handle=Handle("OtherHandle"), container=other_c)
cabinet1 = Cabinet(container=c1, drawers=[drawer1, drawer2])
views = [drawer1, cabinet1]

# Query: find the cabinet that has a drawer whose handle is named "Handle1"
drawer_pattern = the(entity_matching(Drawer, views)(handle=match(Handle)(name="Handle1")))
cabinet_query = the(entity_matching(Cabinet, views)(drawers=match_any(drawer_pattern)))

found_cabinet = cabinet_query.evaluate()
print(found_cabinet.container.name, found_cabinet.drawers[0].handle.name)
```

## Selecting elements from collections with `select_any()`

If you want to retrieve a specific element from a collection attribute while matching, use `select_any(Type)`.
It behaves like `match_any(Type)` but also selects the matched element so you can access it in the result.

```{code-cell} ipython3
from krrood.entity_query_language.match import select_any

selected_drawer = select_any(Drawer)
cabinet_with_selected_drawer = the(
    entity_matching(Cabinet, views)(
        drawers=selected_drawer(handle=match(Handle)(name="Handle1"))
    )
)

ans = cabinet_with_selected_drawer.evaluate()
print(ans[selected_drawer].handle.name)
```

## Selecting inner objects with `select()`

Use `select(Type)` when you want the matched inner objects to appear in the result. The evaluation then
returns a mapping from the selected variables to the concrete objects (a unification dictionary).

```{code-cell} ipython3
from krrood.entity_query_language.match import select

container, handle = select(Container), select(Handle)
fixed_connection_query = the(
    entity_matching(FixedConnection, world.connections)(
        parent=container(name="Container1"),
        child=handle(name="Handle1"),
    )
)

answers = fixed_connection_query.evaluate()
print(answers[container].name, answers[handle].name)
```

## Existential matches in collections with `match_any()`

When matching a container-like attribute (for example, a list), use `match_any(pattern)` to express that
at least one element of the collection should satisfy the given pattern.

Below we add two simple view classes and build a small scene of drawers and a cabinet.

```{code-cell} ipython3
from dataclasses import dataclass
from typing_extensions import List
from krrood.entity_query_language.match import match_any


@dataclass
class Drawer(Symbol):
    handle: Handle
    container: Container


@dataclass
class Cabinet(Symbol):
    container: Container
    drawers: List[Drawer]


# Build a simple set of views
drawer1 = Drawer(handle=h1, container=c1)
drawer2 = Drawer(handle=Handle("OtherHandle"), container=other_c)
cabinet1 = Cabinet(container=c1, drawers=[drawer1, drawer2])
views = [drawer1, cabinet1]

# Query: find the cabinet that has a drawer whose handle is named "Handle1"
drawer_pattern = the(entity_matching(Drawer, views)(handle=match(Handle)(name="Handle1")))
cabinet_query = the(entity_matching(Cabinet, views)(drawers=match_any(drawer_pattern)))

found_cabinet = cabinet_query.evaluate()
print(found_cabinet.container.name, found_cabinet.drawers[0].handle.name)
```

## Selecting elements from collections with `select_any()`

If you want to retrieve a specific element from a collection attribute while matching, use `select_any(Type)`.
It behaves like `match_any(Type)` but also selects the matched element so you can access it in the result.

```{code-cell} ipython3
from krrood.entity_query_language.match import select_any

selected_drawer = select_any(Drawer)
cabinet_with_selected_drawer = the(
    entity_matching(Cabinet, views)(
        drawers=selected_drawer(handle=match(Handle)(name="Handle1"))
    )
)

ans = cabinet_with_selected_drawer.evaluate()
print(ans[selected_drawer].handle.name)
```
