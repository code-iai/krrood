from dataclasses import dataclass
import pytest

from krrood.utils import (
    SubclassJSONSerializer,
    get_full_class_name,
    MissingTypeError,
    InvalidTypeFormatError,
    UnknownModuleError,
    ClassNotFoundError,
    InvalidSubclassError,
)


@dataclass
class Animal(SubclassJSONSerializer):
    """
    Base animal used in tests.
    """

    name: str
    age: int

    def to_json(self):
        data = super().to_json()
        data.update(
            {
                "name": self.name,
                "age": self.age,
            }
        )
        return data

    @classmethod
    def _from_json(cls, data, **kwargs):
        # This will not normally be called, subclasses should handle it.
        return cls(
            name=data["name"],
            age=data.get("age", kwargs.get("default_age", 0)),
        )


@dataclass
class Dog(Animal):
    """
    Dog subtype for tests.
    """

    breed: str = "mixed"

    def to_json(self):
        data = super().to_json()
        data.update(
            {
                "breed": self.breed,
            }
        )
        return data

    @classmethod
    def _from_json(cls, data, **kwargs):
        return cls(
            name=data["name"],
            age=data.get("age", kwargs.get("default_age", 0)),
            breed=data.get("breed", "mixed"),
        )


@dataclass
class Bulldog(Dog):
    """
    Deep subtype to ensure deep discovery works.
    """

    stubborn: bool = True

    def to_json(self):
        data = super().to_json()
        data.update(
            {
                "stubborn": self.stubborn,
            }
        )
        return data

    @classmethod
    def _from_json(cls, data, **kwargs):
        return cls(
            name=data["name"],
            age=data.get("age", kwargs.get("default_age", 0)),
            breed=data.get("breed", "Bulldog"),
            stubborn=data.get("stubborn", True),
        )


@dataclass
class Cat(Animal):
    """
    Cat subtype for tests.
    """

    lives: int = 9

    def to_json(self):
        data = super().to_json()
        data.update(
            {
                "lives": self.lives,
            }
        )
        return data

    @classmethod
    def _from_json(cls, data, **kwargs):
        return cls(
            name=data["name"],
            age=data.get("age", kwargs.get("default_age", 0)),
            lives=data.get("lives", 9),
        )


def test_roundtrip_dog_and_cat():
    dog = Dog(name="Rex", age=5, breed="Shepherd")
    cat = Cat(name="Misty", age=3, lives=7)

    dog_json = dog.to_json()
    cat_json = cat.to_json()

    assert dog_json["type"] == get_full_class_name(Dog)
    assert cat_json["type"] == get_full_class_name(Cat)

    dog2 = SubclassJSONSerializer.from_json(dog_json)
    cat2 = SubclassJSONSerializer.from_json(cat_json)

    assert isinstance(dog2, Dog)
    assert isinstance(cat2, Cat)
    assert dog2 == dog
    assert cat2 == cat


def test_deep_subclass_discovery():
    b = Bulldog(name="Butch", age=4, breed="Bulldog", stubborn=True)
    b_json = b.to_json()

    assert b_json["type"] == get_full_class_name(Bulldog)

    b2 = SubclassJSONSerializer.from_json(b_json)
    assert isinstance(b2, Bulldog)
    assert b2 == b


def test_kwargs_are_forwarded_to_from_json():
    # Age intentionally omitted to test default propagation via kwargs
    partial = {"type": get_full_class_name(Dog), "name": "Pup", "breed": "Beagle"}

    result = SubclassJSONSerializer.from_json(partial, default_age=2)

    assert isinstance(result, Dog)
    assert result.age == 2
    assert result.name == "Pup"
    assert result.breed == "Beagle"


def test_unknown_module_raises_unknown_module_error():
    with pytest.raises(UnknownModuleError):
        SubclassJSONSerializer.from_json({"type": "non.existent.Class"})


def test_missing_type_raises_missing_type_error():
    with pytest.raises(MissingTypeError):
        SubclassJSONSerializer.from_json({})


def test_invalid_type_format_raises_invalid_type_format_error():
    with pytest.raises(InvalidTypeFormatError):
        SubclassJSONSerializer.from_json({"type": "NotAQualifiedName"})


essential_existing_module = "krrood.utils"


def test_class_not_found_raises_class_not_found_error():
    with pytest.raises(ClassNotFoundError):
        SubclassJSONSerializer.from_json({"type": f"{essential_existing_module}.DoesNotExist"})


def test_invalid_subclass_raises_invalid_subclass_error():
    with pytest.raises(InvalidSubclassError):
        SubclassJSONSerializer.from_json({"type": "builtins.object"})
