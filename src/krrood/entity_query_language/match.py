from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Generic, Optional, Type, Dict, Any, List, Union, Self, Iterable

from krrood.entity_query_language.entity import for_all
from krrood.entity_query_language.symbolic import ForAll, Exists

from .failures import NoneWrappedFieldError
from ..class_diagrams.wrapped_field import WrappedField
from .entity import (
    ConditionType,
    contains,
    in_,
    flatten,
    let,
    set_of,
    entity,
    DomainType,
    exists,
)
from .hashed_data import T, HashedValue
from .predicate import HasType
from .symbolic import (
    CanBehaveLikeAVariable,
    Attribute,
    Comparator,
    Flatten,
    QueryObjectDescriptor,
    Variable,
    Selectable,
    SymbolicExpression,
    OperationResult,
    Literal,
    SetOf,
    Entity,
)
from .utils import is_iterable


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
    Whether the match is an existential match check or not.
    """
    universal: bool = field(default=False, kw_only=True)
    """
    Whether the match is a universal match (i.e., must match for all values of the variable/attribute) check or not.
    """

    def __call__(self, **kwargs) -> Union[Self, T, CanBehaveLikeAVariable[T]]:
        """
        Update the match with new keyword arguments to constrain the type we are matching with.

        :param kwargs: The keyword arguments to match against.
        :return: The current match instance after updating it with the new keyword arguments.
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
            attr = self._get_attribute_and_update_selected_variables(
                attr_name, attr_assigned_value
            )
            if self.is_an_unresolved_match(attr_assigned_value):
                self._resolve_child_match_and_merge_conditions(
                    attr, attr_assigned_value
                )
            else:
                self._add_proper_conditions_for_an_already_resolved_child_match(
                    attr, attr_assigned_value
                )

    def _get_attribute_and_update_selected_variables(
        self, attr_name: str, attr_assigned_value: Any
    ) -> Union[Attribute, Flatten]:
        """
        Get the attribute from the variable and update the selected variables with the attribute.

        :param attr_name: The name of the attribute to get.
        :param attr_assigned_value: The assigned value of the attribute.
        :return: The attribute.
        """
        attr: Attribute = getattr(self.variable, attr_name)
        if not attr._wrapped_field_:
            raise NoneWrappedFieldError(self.variable._type_, attr_name)
        if isinstance(attr_assigned_value, Select):
            attr = self._update_attribute_and_selected_variables(
                attr, attr_assigned_value
            )
        return attr

    def _update_attribute_and_selected_variables(
        self, attr: Attribute, attr_assigned_value: Select
    ) -> Union[Attribute, Flatten]:
        """
        Update the attribute by flattening it if it is iterable, and update the selected variables with the attribute.

        :param attr: The attribute to update.
        :param attr_assigned_value: The assigned value of the attribute.
        :return: The updated attribute..
        """
        if attr._is_iterable_:
            attr = flatten(attr)
        self._update_selected_variables(attr)
        attr_assigned_value.update_selected_variable(attr)
        return attr

    @staticmethod
    def is_an_unresolved_match(value: Any) -> bool:
        """
        Check whether the given value is an unresolved Match instance.

        :param value: The value to check.
        :return: True if the value is an unresolved Match instance, else False.
        """
        return isinstance(value, Match) and not value.variable

    def _resolve_child_match_and_merge_conditions(
        self,
        attr: Attribute,
        attr_assigned_value: Match,
    ):
        """
        Resolve the child match and merge the conditions with the parent match.

        :param attr: A symbolic attribute of this match variable.
        :param attr_assigned_value: The assigned value of the attribute, which is a Match instance.
        """
        type_filter_needed = self._is_type_filter_needed(attr, attr_assigned_value)
        if attr._is_iterable_ and (attr_assigned_value.kwargs or type_filter_needed):
            attr = flatten(attr)
        attr_assigned_value._resolve(attr, self)
        if type_filter_needed:
            self._add_type_filter(attr, attr_assigned_value)
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

    def _add_proper_conditions_for_an_already_resolved_child_match(
        self,
        attr: Attribute,
        attr_assigned_value: Any,
    ):
        """
        Add proper conditions for an already resolved child match. These could be an equal, or a containment condition.

        :param attr: A symbolic attribute of this match variable.
        :param attr_assigned_value:  The assigned value of the attribute, which can be a Match instance.
        """
        condition = self._get_either_a_containment_or_an_equal_condition(
            attr, attr_assigned_value
        )
        condition = self._update_condition_if_existential(
            attr, attr_assigned_value, condition
        )
        self.conditions.append(condition)

    def _update_condition_if_existential(
        self,
        attr: Union[Attribute, Flatten],
        attr_assigned_value: Any,
        condition: Comparator,
    ) -> Union[Comparator, Exists, ForAll]:
        """
        Update the condition depending if it is an existential.

        :param attr: The attribute on which the condition is applied.
        :param condition: The condition to update.
        :return: The updated condition.
        """
        if isinstance(attr_assigned_value, Match) and attr_assigned_value.existential:
            attr = attr if not isinstance(attr, Flatten) else attr._child_
            condition = exists(attr, condition)
        return condition

    def _get_either_a_containment_or_an_equal_condition(
        self,
        attr: Attribute,
        assigned_value: Any,
    ) -> Comparator:
        """
        Find and return the appropriate condition for the attribute and its assigned value. This can be one of contains,
        in_, or == depending on the type of the assigned value and the type of the attribute.

        :param attr: The attribute to check.
        :param assigned_value: The value assigned to the attribute.
        :return: A comparator expression representing the condition.
        """
        assigned_variable = (
            assigned_value.variable
            if isinstance(assigned_value, Match)
            else assigned_value
        )
        universal = isinstance(assigned_value, Match) and assigned_value.universal
        if self._attribute_is_iterable_while_the_value_is_not(assigned_value, attr):
            return contains(attr, assigned_variable)
        elif self._value_is_iterable_while_the_attribute_is_not(assigned_value, attr):
            return in_(attr, assigned_variable)
        elif (
            attr._is_iterable_
            and self._is_iterable_value(assigned_value)
            and not universal
        ):
            flat_attr = flatten(attr) if not isinstance(attr, Flatten) else attr
            return contains(assigned_variable, flat_attr)
        else:
            return attr == assigned_variable

    def _attribute_is_iterable_while_the_value_is_not(
        self,
        assigned_value: Any,
        attr: Union[Flatten, Attribute],
    ) -> bool:
        """
        Return True if the attribute is iterable while the assigned value is not an iterable.

        :param assigned_value: The value assigned to the attribute.
        :param attr: The attribute to check.
        """
        return attr._is_iterable_ and not self._is_iterable_value(assigned_value)

    def _value_is_iterable_while_the_attribute_is_not(
        self,
        assigned_value: Any,
        attr: Union[Flatten, Attribute],
    ) -> bool:
        """
        Return True if the assigned value is iterable while the attribute is not an iterable.

        :param assigned_value: The value assigned to the attribute.
        :param attr: The attribute to check.
        """
        return not attr._is_iterable_ and self._is_iterable_value(assigned_value)

    @staticmethod
    def _is_iterable_value(value) -> bool:
        """
        Whether the value is an iterable or a Match instance with an iterable type.

        :param value: The value to check.
        :return: True if the value is an iterable or a Match instance with an iterable type, else False.
        """
        if isinstance(value, CanBehaveLikeAVariable):
            return value._is_iterable_
        elif not isinstance(value, Match) and is_iterable(value):
            return True
        elif isinstance(value, Match) and value._is_iterable_value(value.variable):
            return True
        return False

    def _add_type_filter(
        self,
        attr: Attribute,
        attr_match: Match,
    ):
        """
        Adds a type filter to the match.

        :param attr: The attribute to filter.
        :param attr_match:The Match instance of the attribute.
        """
        self.conditions.append(HasType(attr, attr_match.type_))

    @staticmethod
    def _is_type_filter_needed(attr: Attribute, attr_match: Match):
        attr_type = attr._type_
        return (not attr_type) or (
            (attr_match.type_ and attr_match.type_ is not attr_type)
            and issubclass(attr_match.type_, attr_type)
        )

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
        if not self._var_:
            self.update_selected_variable(self.variable)

    def update_selected_variable(self, variable: CanBehaveLikeAVariable):
        """
        Update the selected variable with the given one.
        """
        self._var_ = variable

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


def match(
    type_: Union[Type[T], CanBehaveLikeAVariable[T], Any, None] = None,
) -> Union[Type[T], CanBehaveLikeAVariable[T], Match[T]]:
    """
    Create and return a Match instance that looks for the pattern provided by the type and the
    keyword arguments.

    :param type_: The type of the variable (i.e., The class you want to instantiate).
    :return: The Match instance.
    """
    return _match_or_select(Match, type_)


def match_any(
    type_: Union[Type[T], CanBehaveLikeAVariable[T], Any, None] = None,
) -> Union[Type[T], CanBehaveLikeAVariable[T], Match[T]]:
    """
    Equivalent to match(type_) but for existential checks.
    """
    match_ = match(type_)
    match_.existential = True
    return match_


def match_all(
    type_: Union[Type[T], CanBehaveLikeAVariable[T], Any, None] = None,
) -> Union[Type[T], CanBehaveLikeAVariable[T], Match[T]]:
    """
    Equivalent to match(type_) but for universal checks.
    """
    match_ = match(type_)
    match_.universal = True
    return match_


def select(
    type_: Union[Type[T], CanBehaveLikeAVariable[T], Any, None] = None,
) -> Union[Type[T], CanBehaveLikeAVariable[T], Select[T]]:
    """
    Equivalent to match(type_) and selecting the variable to be included in the result.
    """
    return _match_or_select(Select, type_)


def select_any(
    type_: Union[Type[T], CanBehaveLikeAVariable[T], Any, None] = None,
) -> Union[Type[T], CanBehaveLikeAVariable[T], Select[T]]:
    """
    Equivalent to select(type_) but for existential checks.
    """
    select_ = select(type_)
    select_.existential = True
    return select_


def select_all(
    type_: Union[Type[T], CanBehaveLikeAVariable[T], Any, None] = None,
) -> Union[Type[T], CanBehaveLikeAVariable[T], Select[T]]:
    """
    Equivalent to select(type_) but for universal checks.
    """
    select_ = select(type_)
    select_.universal = True
    return select_


def _match_or_select(
    match_type: Type[Match],
    type_: Union[Type[T], CanBehaveLikeAVariable[T], Any, None] = None,
) -> Union[Type[T], CanBehaveLikeAVariable[T], Match[T]]:
    """
    Create and return a Match/Select instance that looks for the pattern provided by the type and the
    keyword arguments.
    """
    if isinstance(type_, CanBehaveLikeAVariable):
        return Select(type_._type_, variable=type_)
    elif type_ and not isinstance(type_, type):
        return match_type(type_=type_, variable=Literal(type_))
    return match_type(type_)


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


EntityType = Union[SetOf[T], Entity[T], T, Iterable[T], Type[T], Match[T]]
"""
The possible types for entities.
"""
