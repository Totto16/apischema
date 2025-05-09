from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from jsonschema import Draft202012Validator
from apischema.aliases import alias
from graphql.utilities import print_schema

from apischema import schema, type_name
from apischema.graphql import graphql_schema
from apischema.json_schema import deserialization_schema, serialization_schema
from apischema.typing import Annotated


@dataclass
class A:
    a: Annotated[
        int,
        schema(max=10),
        schema(description="type description"),
        type_name("someInt"),
        schema(description="field description"),
    ] = field(metadata=schema(min=0))


def a() -> A:  # type: ignore
    ...


def test_annotated_schema():
    assert (
        deserialization_schema(A)
        == serialization_schema(A)
        == {
            "$schema": "http://json-schema.org/draft/2020-12/schema#",
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "maximum": 10,
                    "minimum": 0,
                    "description": "field description",
                }
            },
            "required": ["a"],
            "additionalProperties": False,
        }
    )
    assert (
        deserialization_schema(A, all_refs=True)
        == serialization_schema(A, all_refs=True)
        == {
            "$schema": "http://json-schema.org/draft/2020-12/schema#",
            "$ref": "#/$defs/A",
            "$defs": {
                "A": {
                    "additionalProperties": False,
                    "properties": {
                        "a": {
                            "$ref": "#/$defs/someInt",
                            "description": "field description",
                            "minimum": 0,
                        }
                    },
                    "required": ["a"],
                    "type": "object",
                },
                "someInt": {
                    "description": "type description",
                    "maximum": 10,
                    "type": "integer",
                },
            },
        }
    )
    assert (
        print_schema(graphql_schema(query=[a]))
        == '''\
type Query {
  a: A!
}

type A {
  """field description"""
  a: someInt!
}

"""type description"""
scalar someInt'''
    )


class AllTypes(str, Enum):
    type1 = "type1"
    type2 = "type2"


@dataclass
class BaseClassA:
    typ: AllTypes


@dataclass
class ClassA1(BaseClassA):
    typ: Literal[AllTypes.type1]
    a_member: int


@dataclass
class ClassA2(BaseClassA):
    typ: Literal[AllTypes.type2]
    b_member: str


@dataclass(slots=True)
class BaseClassB:
    __typ: AllTypes = field(metadata=alias("type"))


@dataclass(slots=True)
class ClassB1(BaseClassB):
    __typ: Literal[AllTypes.type1] = field(metadata=alias("type"))
    a_member: int


@dataclass(slots=True)
class ClassB2(BaseClassB):
    __typ: Literal[AllTypes.type2] = field(metadata=alias("type"))
    b_member: str


def test_advanced_schema():
    assert (
        Draft202012Validator.check_schema(serialization_schema(ClassA1 | ClassA2))
        is None
        and Draft202012Validator.check_schema(deserialization_schema(ClassA1 | ClassA2))
        is None
    )
    assert (
        deserialization_schema(ClassA1 | ClassA2)
        == serialization_schema(ClassA1 | ClassA2)
        == {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "typ": {"type": "string", "const": AllTypes.type1},
                        "a_member": {"type": "integer"},
                    },
                    "required": ["typ", "a_member"],
                    "additionalProperties": False,
                },
                {
                    "type": "object",
                    "properties": {
                        "typ": {"type": "string", "const": AllTypes.type2},
                        "b_member": {"type": "string"},
                    },
                    "required": ["typ", "b_member"],
                    "additionalProperties": False,
                },
            ],
            "$schema": "http://json-schema.org/draft/2020-12/schema#",
        }
    )
    assert (
        Draft202012Validator.check_schema(serialization_schema(ClassB1 | ClassB2))
        is None
        and Draft202012Validator.check_schema(deserialization_schema(ClassB1 | ClassB2))
        is None
    )
    assert (
        deserialization_schema(ClassB1 | ClassB2)
        == serialization_schema(ClassB1 | ClassB2)
        == {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "const": AllTypes.type1},
                        "a_member": {"type": "integer"},
                    },
                    "required": ["type", "a_member"],
                    "additionalProperties": False,
                },
                {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "const": AllTypes.type2},
                        "b_member": {"type": "string"},
                    },
                    "required": ["type", "b_member"],
                    "additionalProperties": False,
                },
            ],
            "$schema": "http://json-schema.org/draft/2020-12/schema#",
        }
    )
    assert (
        Draft202012Validator.check_schema(
            serialization_schema(ClassB1 | ClassB2, all_refs=True)
        )
        is None
        and Draft202012Validator.check_schema(
            deserialization_schema(ClassB1 | ClassB2, all_refs=True)
        )
        is None
    )
    print(deserialization_schema(ClassB1 | ClassB2, all_refs=True))
    assert (
        deserialization_schema(ClassB1 | ClassB2, all_refs=True)
        == serialization_schema(ClassB1 | ClassB2, all_refs=True)
        == {
            "anyOf": [{"$ref": "#/$defs/ClassB1"}, {"$ref": "#/$defs/ClassB2"}],
            "$defs": {
                "ClassB1": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "const": AllTypes.type1},
                        "a_member": {"type": "integer"},
                    },
                    "required": ["type", "a_member"],
                    "additionalProperties": False,
                },
                "ClassB2": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "const": AllTypes.type2},
                        "b_member": {"type": "string"},
                    },
                    "required": ["type", "b_member"],
                    "additionalProperties": False,
                },
            },
            "$schema": "http://json-schema.org/draft/2020-12/schema#",
        }
    )
