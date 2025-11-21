from __future__ import annotations

import importlib
from dataclasses import dataclass
from json import JSONDecodeError

from typing_extensions import Dict, Any, Self, Union
import json
import uuid

from krrood.utils import get_full_class_name

JSON_TYPE_NAME = "__json_type__"  # the key used in JSON dicts to identify the class


class JSONSerializationError(Exception):
    """Base exception for JSON (de)serialization errors."""


class MissingTypeError(JSONSerializationError):
    """Raised when the 'type' field is missing in the JSON data."""

    def __init__(self):
        super().__init__("Missing 'type' field in JSON data")


@dataclass
class InvalidTypeFormatError(JSONSerializationError):
    """Raised when the 'type' field value is not a fully qualified class name."""

    invalid_type_value: str

    def __post_init__(self):
        super().__init__(f"Invalid type format: {self.invalid_type_value}")


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


class SubclassJSONSerializer:
    """
    Class for automatic (de)serialization of subclasses using importlib.

    Stores the fully qualified class name in `type` during serialization and
    imports that class during deserialization.
    """

    def to_json(self) -> Dict[str, Any]:
        return {JSON_TYPE_NAME: get_full_class_name(self.__class__)}

    @classmethod
    def _from_json(cls, data: Dict[str, Any], **kwargs) -> Self:
        """
        Create an instance from a json dict.
        This method is called from the from_json method after the correct subclass is determined and should be
        overwritten by the subclass.

        :param data: The JSON dict
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
        fully_qualified_class_name = data.get(JSON_TYPE_NAME)
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

        return target_cls._from_json(data, **kwargs)


class SubclassJSONEncoder(json.JSONEncoder):
    """
    Custom encoder to handle classes that inherit from SubClassJSONEncoder and UUIDs.
    """

    def default(self, obj):

        # handle objects that are duck-typed like SubclassJSONSerializer
        if hasattr(obj, "to_json"):
            return obj.to_json()

        # Let the base class handle other objects
        return json.JSONEncoder.default(self, obj)


class SubclassJSONDecoder(json.JSONDecoder):
    """
    Custom decoder to handle classes that inherit from SubClassJSONSerializer and UUIDs.
    """

    def decode(self, s, _w=json.decoder.WHITESPACE.match):
        if not isinstance(s, dict):
            obj = super().decode(s, _w)
        else:
            obj = s
        return self._deserialize_nested(obj)

    def _deserialize_nested(self, obj):
        """
        Recursively deserialize nested objects.
        """
        if isinstance(obj, dict):
            if JSON_TYPE_NAME in obj:
                return SubclassJSONSerializer.from_json(obj)
            else:
                return {k: self._deserialize_nested(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deserialize_nested(item) for item in obj]
        else:
            return obj


def to_json(obj: Union[SubclassJSONSerializer, Any]) -> str:
    """
    Serialize an object to a JSON string.
    This is a drop-in replacement for json.dumps which handles SubclassJSONSerializer-like objects.

    :param obj: The object to serialize
    :return: The JSON string
    """
    return json.dumps(obj, cls=SubclassJSONEncoder)


def from_json(data: str) -> Union[SubclassJSONSerializer, Any]:
    """
    Deserialize a JSON string to an object.
    This is a drop-in replacement for json.loads which handles SubclassJSONSerializer-like objects.

    :param data: The JSON string
    :return: The deserialized object
    """

    # If we already have a Python container, recursively deserialize nested subclass payloads
    if isinstance(data, dict) or isinstance(data, list):
        decoder = SubclassJSONDecoder()
        return decoder._deserialize_nested(data)

    # If it is not a string (e.g., int, float, bool, None), return as-is
    if not isinstance(data, str):
        return data

    # It is a string: try to parse as JSON; if that fails, treat it as a raw string
    try:
        return json.loads(data, cls=SubclassJSONDecoder)
    except JSONDecodeError:
        return data


# %% Monkey patch UUID to behave like SubclassJSONSerializer
def uuid_from_json(data):
    return uuid.UUID(data["value"])


def uuid_to_json(obj):
    return {**SubclassJSONSerializer.to_json(obj), "value": str(obj)}


uuid.UUID._from_json = lambda data: uuid_from_json(data)
uuid.UUID.to_json = lambda self: uuid_to_json(self)
