from __future__ import annotations

import importlib
from dataclasses import dataclass
from functools import lru_cache
from typing import Type, List

from typing_extensions import Dict, Any, Self


@lru_cache(maxsize=None)
def recursive_subclasses(cls: Type) -> List[Type]:
    """
    :param cls: The class.
    :return: A list of the classes subclasses without the class itself.
    """
    return cls.__subclasses__() + [
        g for s in cls.__subclasses__() for g in recursive_subclasses(s)
    ]


def get_full_class_name(cls):
    """
    Returns the full name of a class, including the module name.

    :param cls: The class.
    :return: The full name of the class
    """
    return cls.__module__ + "." + cls.__name__


class JSONSerializationError(Exception):
    """Base exception for JSON (de)serialization errors."""


class MissingTypeError(JSONSerializationError):
    """Raised when the 'type' field is missing in the JSON data."""

    def __init__(self):
        super().__init__("Missing 'type' field in JSON data")


@dataclass
class InvalidTypeFormatError(JSONSerializationError):
    """Raised when the 'type' field value is not a fully qualified class name."""

    fully_qualified_class_name: str

    def __post_init__(self):
        super().__init__(f"Invalid type format: {self.fully_qualified_class_name}")


@dataclass
class UnknownModuleError(JSONSerializationError):
    """Raised when the module specified in the 'type' field cannot be imported."""

    module_name: str

    def __post_init__(self):
        super().__init__(f"Unknown module in type: {self.module_name}")


@dataclass
class ClassNotFoundError(JSONSerializationError):
    """Raised when the class specified in the 'type' field cannot be found in the module."""

    class_name: str
    module_name: str

    def __post_init__(self):
        super().__init__(
            f"Class '{self.class_name}' not found in module '{self.module_name}'"
        )


@dataclass
class InvalidSubclassError(JSONSerializationError):
    """Raised when the resolved class is not a SubclassJSONSerializer subclass."""

    fully_qualified_class_name: str

    def __post_init__(self):
        super().__init__(
            f"Resolved type {self.fully_qualified_class_name} is not a SubclassJSONSerializer"
        )


class SubclassJSONSerializer:
    """
    Class for automatic (de)serialization of subclasses using importlib.

    Stores the fully qualified class name in `type` during serialization and
    imports that class during deserialization.
    """

    def to_json(self) -> Dict[str, Any]:
        return {"type": get_full_class_name(self.__class__)}

    @classmethod
    def _from_json(cls, data: Dict[str, Any], **kwargs) -> Self:
        """
        Create an instance from a json dict.
        This method is called from the from_json method after the correct subclass is determined and should be
        overwritten by the subclass.

        :param data: The json dict
        :param kwargs: Additional keyword arguments to pass to the constructor of the subclass.
        :return: The deserialized object
        """
        raise NotImplementedError()

    @classmethod
    def from_json(cls, data: Dict[str, Any], **kwargs) -> Self:
        """
        Create the correct instanceof the subclass from a json dict.

        :param data: The json dict
        :param kwargs: Additional keyword arguments to pass to the constructor of the subclass.
        :return: The correct instance of the subclass
        """
        fully_qualified_class_name = data.get("type")
        if not fully_qualified_class_name:
            raise MissingTypeError()

        try:
            module_name, class_name = fully_qualified_class_name.rsplit(".", 1)
        except ValueError as exc:
            raise InvalidTypeFormatError(fully_qualified_class_name) from exc

        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            raise UnknownModuleError(module_name) from exc

        try:
            target_cls = getattr(module, class_name)
        except AttributeError as exc:
            raise ClassNotFoundError(class_name, module_name) from exc

        if not issubclass(target_cls, SubclassJSONSerializer):
            raise InvalidSubclassError(fully_qualified_class_name)

        return target_cls._from_json(data, **kwargs)
