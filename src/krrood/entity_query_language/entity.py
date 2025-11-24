from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property

from .hashed_data import T, HashedValue
from .symbol_graph import SymbolGraph
from .utils import is_iterable, is_iterable_type
from ..class_diagrams.wrapped_field import WrappedField

"""
User interface (grammar & vocabulary) for entity query language.
"""
import operator

from typing_extensions import (
    Any,
    Optional,
    Union,
    Iterable,
    Dict,
    Generic,
    Type,
    Tuple,
    List,
    Callable,
    Self,
)

from .symbolic import (
    SymbolicExpression,
    Entity,
    SetOf,
    The,
    An,
    AND,
    Comparator,
    chained_logic,
    CanBehaveLikeAVariable,
    From,
    Variable,
    optimize_or,
    Flatten,
    ForAll,
    Exists,
    Literal,
    ResultQuantifier,
    Attribute,
    QueryObjectDescriptor,
    Selectable,
    OperationResult,
)
from .result_quantification_constraint import ResultQuantificationConstraint

from .predicate import (
    Predicate,
    # type: ignore
    Symbol,  # type: ignore
    HasType,
)


ConditionType = Union[SymbolicExpression, bool, Predicate]
"""
The possible types for conditions.
"""
EntityType = Union[SetOf[T], Entity[T], T, Iterable[T], Type[T]]
"""
The possible types for entities.
"""


def an(
    entity_: EntityType,
    quantification: Optional[ResultQuantificationConstraint] = None,
) -> Union[An[T], T]:
    """
    Select a single element satisfying the given entity description.

    :param entity_: An entity or a set expression to quantify over.
    :param quantification: Optional quantification constraint.
    :return: A quantifier representing "an" element.
    :rtype: An[T]
    """
    return _quantify_entity(An, entity_, _quantification_constraint_=quantification)


a = an
"""
This is an alias to accommodate for words not starting with vowels.
"""


def the(
    entity_: EntityType,
) -> Union[The[T], T]:
    """
    Select the unique element satisfying the given entity description.

    :param entity_: An entity or a set expression to quantify over.
    :return: A quantifier representing "an" element.
    :rtype: The[T]
    """
    return _quantify_entity(The, entity_)


def _quantify_entity(
    quantifier: Type[ResultQuantifier], entity_: EntityType, **quantifier_kwargs
) -> Union[ResultQuantifier[T], T]:
    """
    Apply the given quantifier to the given entity.

    :param quantifier: The quantifier to apply.
    :param entity_: The entity to quantify.
    :param quantifier_kwargs: Keyword arguments to pass to the quantifier.
    :return: The quantified entity.
    """
    if isinstance(entity_, Match):
        entity_ = entity_.expression
    return quantifier(entity_, **quantifier_kwargs)


def entity(
    selected_variable: T,
    *properties: ConditionType,
) -> Entity[T]:
    """
    Create an entity descriptor from a selected variable and its properties.

    :param selected_variable: The variable to select in the result.
    :type selected_variable: T
    :param properties: Conditions that define the entity.
    :type properties: Union[SymbolicExpression, bool]
    :return: Entity descriptor.
    :rtype: Entity[T]
    """
    selected_variables, expression = _extract_variables_and_expression(
        [selected_variable], *properties
    )
    return Entity(selected_variables=selected_variables, _child_=expression)


def set_of(
    selected_variables: Iterable[T],
    *properties: ConditionType,
) -> SetOf[T]:
    """
    Create a set descriptor from selected variables and their properties.

    :param selected_variables: Iterable of variables to select in the result set.
    :type selected_variables: Iterable[T]
    :param properties: Conditions that define the set.
    :type properties: Union[SymbolicExpression, bool]
    :return: Set descriptor.
    :rtype: SetOf[T]
    """
    selected_variables, expression = _extract_variables_and_expression(
        selected_variables, *properties
    )
    return SetOf(selected_variables=selected_variables, _child_=expression)


def _extract_variables_and_expression(
    selected_variables: Iterable[T], *properties: ConditionType
) -> Tuple[List[T], SymbolicExpression]:
    """
    Extracts the variables and expressions from the selected variables.

    :param selected_variables: Iterable of variables to select in the result set.
    :param properties: Conditions on the selected variables.
    :return: Tuple of selected variables and expressions.
    """
    expression_list = list(properties)
    selected_variables = list(selected_variables)
    expression = None
    if len(expression_list) > 0:
        expression = (
            and_(*expression_list) if len(expression_list) > 1 else expression_list[0]
        )
    return selected_variables, expression


DomainType = Union[Iterable, None]


def let(
    type_: Type[T],
    domain: DomainType,
    name: Optional[str] = None,
) -> Union[T, CanBehaveLikeAVariable[T], Variable[T]]:
    """
    Declare a symbolic variable that can be used inside queries.

    Filters the domain to elements that are instances of T.

    .. warning::

        If no domain is provided, and the type_ is a Symbol type, then the domain will be inferred from the SymbolGraph,
         which may contain unnecessarily many elements.

    :param type_: The type of variable.
    :param domain: Iterable of potential values for the variable or None.
     If None, the domain will be inferred from the SymbolGraph for Symbol types, else should not be evaluated by EQL
      but by another evaluator (e.g., EQL To SQL converter in Ormatic).
    :param name: The variable name, only required for pretty printing.
    :return: A Variable that can be queried for.
    """
    domain_source = _get_domain_source_from_domain_and_type_values(domain, type_)

    if name is None:
        name = type_.__name__

    result = Variable(
        _type_=type_,
        _domain_source_=domain_source,
        _name__=name,
    )

    return result


def _get_domain_source_from_domain_and_type_values(
    domain: DomainType, type_: Type
) -> Optional[From]:
    """
    Get the domain source from the domain and the type values.

    :param domain: The domain value.
    :param type_: The type of the variable.
    :return: The domain source as a From object.
    """
    if is_iterable(domain):
        domain = filter(lambda x: isinstance(x, type_), domain)
    elif domain is None and issubclass(type_, Symbol):
        domain = SymbolGraph().get_instances_of_type(type_)
    return From(domain)


def and_(*conditions: ConditionType):
    """
    Logical conjunction of conditions.

    :param conditions: One or more conditions to combine.
    :type conditions: SymbolicExpression | bool
    :return: An AND operator joining the conditions.
    :rtype: SymbolicExpression
    """
    return chained_logic(AND, *conditions)


def or_(*conditions):
    """
    Logical disjunction of conditions.

    :param conditions: One or more conditions to combine.
    :type conditions: SymbolicExpression | bool
    :return: An OR operator joining the conditions.
    :rtype: SymbolicExpression
    """
    return chained_logic(optimize_or, *conditions)


def not_(operand: SymbolicExpression):
    """
    A symbolic NOT operation that can be used to negate symbolic expressions.
    """
    if not isinstance(operand, SymbolicExpression):
        operand = Literal(operand)
    return operand.__invert__()


def contains(
    container: Union[Iterable, CanBehaveLikeAVariable[T]], item: Any
) -> Comparator:
    """
    Check whether a container contains an item.

    :param container: The container expression.
    :param item: The item to look for.
    :return: A comparator expression equivalent to ``item in container``.
    :rtype: SymbolicExpression
    """
    return in_(item, container)


def in_(item: Any, container: Union[Iterable, CanBehaveLikeAVariable[T]]):
    """
    Build a comparator for membership: ``item in container``.

    :param item: The candidate item.
    :param container: The container expression.
    :return: Comparator expression for membership.
    :rtype: Comparator
    """
    return Comparator(container, item, operator.contains)


def flatten(
    var: Union[CanBehaveLikeAVariable[T], Iterable[T]],
) -> Union[CanBehaveLikeAVariable[T], T]:
    """
    Flatten a nested iterable domain into individual items while preserving the parent bindings.
    This returns a DomainMapping that, when evaluated, yields one solution per inner element
    (similar to SQL UNNEST), keeping existing variable bindings intact.
    """
    return Flatten(var)


def for_all(
    universal_variable: Union[CanBehaveLikeAVariable[T], T],
    condition: ConditionType,
):
    """
    A universal on variable that finds all sets of variable bindings (values) that satisfy the condition for **every**
     value of the universal_variable.

    :param universal_variable: The universal on variable that the condition must satisfy for all its values.
    :param condition: A SymbolicExpression or bool representing a condition that must be satisfied.
    :return: A SymbolicExpression that can be evaluated producing every set that satisfies the condition.
    """
    return ForAll(universal_variable, condition)


def exists(
    universal_variable: Union[CanBehaveLikeAVariable[T], T],
    condition: ConditionType,
):
    """
    A universal on variable that finds all sets of variable bindings (values) that satisfy the condition for **any**
     value of the universal_variable.

    :param universal_variable: The universal on variable that the condition must satisfy for any of its values.
    :param condition: A SymbolicExpression or bool representing a condition that must be satisfied.
    :return: A SymbolicExpression that can be evaluated producing every set that satisfies the condition.
    """
    return Exists(universal_variable, condition)


def inference(
    type_: Type[T],
) -> Union[Type[T], Callable[[Any], Variable[T]]]:
    """
    This returns a factory function that creates a new variable of the given type and takes keyword arguments for the
    type constructor.

    :param type_: The type of the variable (i.e., The class you want to instantiate).
    :return: The factory function for creating a new variable.
    """
    return lambda **kwargs: Variable(
        _type_=type_, _name__=type_.__name__, _kwargs_=kwargs, _is_inferred_=True
    )


@dataclass
class Match(Generic[T]):
    """
    Construct a query that looks for the pattern provided by the type and the keyword arguments.
    """

    type_: Optional[Type[T]] = None
    """
    The type of the variable.
    """
    kwargs: Dict[str, Any] = field(init=False, default_factory=dict)
    """
    The keyword arguments to match against.
    """
    variable: Optional[CanBehaveLikeAVariable[T]] = field(kw_only=True, default=None)
    """
    The created variable from the type and kwargs.
    """
    conditions: List[ConditionType] = field(init=False, default_factory=list)
    """
    The conditions that define the match.
    """
    _resolved: bool = field(init=False, default=False)
    """
    Whether the match has been resolved.
    """
    selected_variables: List[CanBehaveLikeAVariable] = field(
        init=False, default_factory=list
    )
    """
    A list of selected attributes.
    """
    parent: Optional[Match] = field(init=False, default=None)
    """
    The parent match if this is a nested match.
    """
    is_selected: bool = field(default=False, kw_only=True)
    """
    Whether the variable should be selected in the result.
    """
    existential: bool = field(default=False, kw_only=True)
    """
    Whether the match is an existential match check or find all matches.
    """
    is_iterable: bool = field(default=False, kw_only=True)
    """
    Whether the match variable is an iterable.
    """

    def __call__(self, **kwargs) -> Union[Self, T, CanBehaveLikeAVariable[T]]:
        """
        Update the match with new keyword arguments to constrain the type we are matching with.

        :param kwargs: The keyword arguments to match against.
        """
        self.kwargs = kwargs
        return self

    def _resolve(
        self,
        variable: Optional[CanBehaveLikeAVariable] = None,
        parent: Optional[Match] = None,
    ):
        """
        Resolve the match by creating the variable and conditions expressions.

        :param variable: An optional pre-existing variable to use for the match; if not provided, a new variable will
         be created.
        :param parent: The parent match if this is a nested match.
        :return:
        """
        self._update_the_match_fields(variable, parent)
        for attr_name, attr_assigned_value in self.kwargs.items():
            attr: Attribute = getattr(self.variable, attr_name)
            attr_wrapped_field = attr._wrapped_field_
            if self.is_an_unresolved_match(attr_assigned_value):
                self._resolve_child_match_and_merge_conditions(
                    attr, attr_assigned_value, attr_wrapped_field
                )
            else:
                if isinstance(attr_assigned_value, Select):
                    self._update_selected_variables(attr_assigned_value.variable)
                self._add_proper_conditions_for_an_already_resolved_child_match(
                    attr, attr_assigned_value, attr_wrapped_field
                )

    @staticmethod
    def is_an_unresolved_match(value: Any) -> bool:
        """
        Check whether the given value is an unresolved Match instance.

        :param value: The value to check.
        :return: True if the value is an unresolved Match instance, else False.
        """
        return isinstance(value, Match) and not value.variable

    def _add_proper_conditions_for_an_already_resolved_child_match(
        self,
        attr: Attribute,
        attr_assigned_value: Any,
        attr_wrapped_field: WrappedField,
    ):
        """
        Add proper conditions for an already resolved child match. These could be an equal, or a containment condition.

        :param attr: A symbolic attribute of this match variable.
        :param attr_assigned_value:  The assigned value of the attribute, which can be a Match instance.
        :param attr_wrapped_field: The WrappedField representing the attribute.
        """
        condition = self._get_either_a_containment_or_an_equal_condition(
            attr, attr_assigned_value, attr_wrapped_field
        )
        self.conditions.append(condition)

    def _resolve_child_match_and_merge_conditions(
        self,
        attr: Attribute,
        attr_assigned_value: Match,
        attr_wrapped_field: WrappedField,
    ):
        """
        Resolve the child match and merge the conditions with the parent match.

        :param attr: A symbolic attribute of this match variable.
        :param attr_assigned_value: The assigned value of the attribute, which is a Match instance.
        :param attr_wrapped_field: The WrappedField representing the attribute.
        """
        attr = self._flatten_the_attribute_if_is_iterable_while_value_is_not(
            attr, attr_assigned_value, attr_wrapped_field
        )
        attr_assigned_value._resolve(attr, self)
        self._add_type_filter_if_needed(attr, attr_assigned_value, attr_wrapped_field)
        self.conditions.extend(attr_assigned_value.conditions)

    def _update_the_match_fields(
        self,
        variable: Optional[CanBehaveLikeAVariable] = None,
        parent: Optional[Match] = None,
    ):
        """
        Update the match variable, parent, is_selected, and type_ fields.

        :param variable: The variable to use for the match.
         If None, a new variable will be created.
        :param parent: The parent match if this is a nested match.
        """
        self.variable = variable if variable else self._get_or_create_variable()
        self.parent = parent
        if self.is_selected:
            self._update_selected_variables(self.variable)
        if not self.type_:
            self.type_ = self.variable._type_

    def _update_selected_variables(self, variable: CanBehaveLikeAVariable):
        """
        Update the selected variables of the match by adding the given variable to the root Match selected variables.
        """
        if self.parent:
            self.parent._update_selected_variables(variable)
        else:
            self.selected_variables.append(variable)

    def _get_either_a_containment_or_an_equal_condition(
        self,
        attr: Attribute,
        assigned_value: Any,
        wrapped_field: Optional[WrappedField] = None,
    ) -> Comparator:
        """
        Find and return the appropriate condition for the attribute and its assigned value. This can be one of contains,
        in_, or == depending on the type of the assigned value and the type of the attribute.

        :param attr: The attribute to check.
        :param assigned_value: The value assigned to the attribute.
        :param wrapped_field: The WrappedField representing the attribute.
        :return: A comparator expression representing the condition.
        """
        assigned_variable = (
            assigned_value.variable
            if isinstance(assigned_value, Match)
            else assigned_value
        )
        if self._attribute_is_iterable_while_the_value_is_not(
            assigned_value, wrapped_field
        ):
            return contains(attr, assigned_variable)
        elif self._value_is_iterable_while_the_attribute_is_not(
            assigned_value, wrapped_field
        ):
            return in_(attr, assigned_variable)
        elif isinstance(assigned_value, Match) and assigned_value.existential:
            return contains(assigned_variable, flatten(attr))
        else:
            return attr == assigned_variable

    def _attribute_is_iterable_while_the_value_is_not(
        self,
        assigned_value: Any,
        wrapped_field: Optional[WrappedField] = None,
    ) -> bool:
        """
        Return True if the attribute is iterable while the assigned value is not an iterable.

        :param assigned_value: The value assigned to the attribute.
        :param wrapped_field: The WrappedField representing the attribute.
        """
        return (
            wrapped_field
            and wrapped_field.is_iterable
            and not self._is_iterable_value(assigned_value)
        )

    def _value_is_iterable_while_the_attribute_is_not(
        self, assigned_value: Any, wrapped_field: Optional[WrappedField] = None
    ) -> bool:
        """
        Return True if the assigned value is iterable while the attribute is not an iterable.

        :param assigned_value: The value assigned to the attribute.
        :param wrapped_field: The WrappedField representing the attribute.
        """
        return (
            wrapped_field
            and not wrapped_field.is_iterable
            and self._is_iterable_value(assigned_value)
        )

    def _flatten_the_attribute_if_is_iterable_while_value_is_not(
        self,
        attr: Attribute,
        attr_assigned_value: Any,
        attr_wrapped_field: Optional[WrappedField] = None,
    ) -> Union[Attribute, Flatten]:
        """
        Apply a flatten operation to the attribute if it is an iterable while the assigned value is not an iterable.

        :param attr: The attribute to flatten.
        :param attr_assigned_value: The value assigned to the attribute.
        :param attr_wrapped_field: The WrappedField representing the attribute.
        :return: The flattened attribute if it is an iterable, else the original attribute.
        """
        if self._is_iterable_value(attr_assigned_value):
            return attr
        if attr_wrapped_field and attr_wrapped_field.is_iterable:
            return flatten(attr)
        return attr

    @staticmethod
    def _is_iterable_value(value) -> bool:
        """
        Whether the value is an iterable or a Match instance with an iterable type.

        :param value: The value to check.
        :return: True if the value is an iterable or a Match instance with an iterable type, else False.
        """
        if isinstance(value, Attribute):
            return value._wrapped_field_.is_iterable
        if not isinstance(value, Match) and is_iterable(value):
            return True
        elif isinstance(value, Match) and value._is_iterable_value(value.variable):
            return True
        return False

    def _add_type_filter_if_needed(
        self,
        attr: Attribute,
        attr_match: Match,
        attr_wrapped_field: Optional[WrappedField] = None,
    ):
        """
        Adds a type filter to the match if needed. Basically when the type hint is not found or when it is
        a superclass of the type provided in the match.

        :param attr: The attribute to filter.
        :param attr_match:The Match instance of the attribute.
        :param attr_wrapped_field: The WrappedField representing the attribute.
        :return:
        """
        attr_type = attr_wrapped_field.type_endpoint if attr_wrapped_field else None
        if (not attr_type) or (
            (attr_match.type_ is not attr_type)
            and issubclass(attr_match.type_, attr_type)
        ):
            self.conditions.append(HasType(attr, attr_match.type_))

    def _get_or_create_variable(self) -> CanBehaveLikeAVariable[T]:
        """
        Create a variable with the given type if
        """
        if self.variable:
            return self.variable
        return let(self.type_, None)

    @cached_property
    def expression(self) -> QueryObjectDescriptor[T]:
        """
        Return the entity expression corresponding to the match query.
        """
        self._resolve()
        if len(self.selected_variables) > 1:
            return set_of(self.selected_variables, *self.conditions)
        else:
            if not self.selected_variables:
                self.selected_variables.append(self.variable)
            return entity(self.selected_variables[0], *self.conditions)


@dataclass
class MatchEntity(Match[T]):
    """
    A match that can also take a domain and should be used as the outermost match in a nested match statement.
    This is because the inner match statements derive their domain from the outer match as they are basically attributes
    of the outer match variable.
    """

    domain: DomainType = None
    """
    The domain to use for the variable created by the match.
    """

    def _get_or_create_variable(self) -> Variable[T]:
        """
        Create a variable with the given type and domain.
        """
        return let(self.type_, self.domain)


@dataclass
class Select(Match[T], Selectable[T]):
    """
    This is a Match with the addition that the matched entity is selected in the result.
    """

    _var_: CanBehaveLikeAVariable[T] = field(init=False)
    is_selected: bool = field(init=False, default=True)

    def __post_init__(self):
        """
        This is needed to prevent the SymbolicExpression __post_init__ from being called which will make a node out of
        this instance, and that is not what we want.
        """
        ...

    def _resolve(
        self,
        variable: Optional[CanBehaveLikeAVariable] = None,
        parent: Optional[Match] = None,
    ):
        super()._resolve(variable, parent)
        self._var_ = self.variable

    def _evaluate__(
        self,
        sources: Optional[Dict[int, HashedValue]] = None,
        parent: Optional[SymbolicExpression] = None,
    ) -> Iterable[OperationResult]:
        yield from self.variable._evaluate__(sources, parent)

    @property
    def _name_(self) -> str:
        return self._var_._name_

    @cached_property
    def _all_variable_instances_(self) -> List[CanBehaveLikeAVariable[T]]:
        return self._var_._all_variable_instances_


MatchType = Union[
    Type[T],
    CanBehaveLikeAVariable[T],
    Callable[..., Union[Match[T], CanBehaveLikeAVariable[T], T]],
]
"""
The types needed for the linter to hint the kwargs for the type construction.
"""
MatchInputType = Union[Type[T], CanBehaveLikeAVariable[T], None]
"""
The input type to the match function.
"""


def match(
    type_: Union[Type[T], CanBehaveLikeAVariable[T], None] = None,
) -> Union[Type[T], CanBehaveLikeAVariable[T], Match[T]]:
    """
    Create and return a Match instance that looks for the pattern provided by the type and the
    keyword arguments.

    :param type_: The type of the variable (i.e., The class you want to instantiate).
    :return: The Match instance.
    """
    if isinstance(type_, CanBehaveLikeAVariable):
        return Match(type_._type_, variable=type_)
    return Match(type_)


def match_any(
    type_: Union[Type[T], CanBehaveLikeAVariable[T], None],
) -> Union[Type[T], CanBehaveLikeAVariable[T], Match[T]]:
    """
    Equivalent to match(type_) but for existential matches.
    """
    match_ = match(type_)
    match_.existential = True
    return match_


def select(
    type_: Union[Type[T], CanBehaveLikeAVariable[T], None] = None,
) -> Union[Type[T], CanBehaveLikeAVariable[T], Select[T]]:
    """
    Equivalent to match(type_) and selecting the variable to be included in the result.
    """
    if isinstance(type_, CanBehaveLikeAVariable):
        return Select(type_._type_, variable=type_)
    return Select(type_)


def select_any(
    type_: Union[Type[T], CanBehaveLikeAVariable[T], None] = None,
) -> Union[Type[T], CanBehaveLikeAVariable[T], Select[T]]:
    """
    Equivalent to match_any(type_) and selecting the variable to be included in the result.
    """
    select_ = select(type_)
    select_.existential = True
    return select_


def entity_matching(
    type_: Union[Type[T], CanBehaveLikeAVariable[T]], domain: DomainType
) -> Union[Type[T], CanBehaveLikeAVariable[T], MatchEntity[T]]:
    """
    Same as :py:func:`krrood.entity_query_language.entity.match` but with a domain to use for the variable created
     by the match.

    :param type_: The type of the variable (i.e., The class you want to instantiate).
    :param domain: The domain used for the variable created by the match.
    :return: The MatchEntity instance.
    """
    return MatchEntity(type_, domain)
