from __future__ import annotations

import datetime
from typing import Dict, Type, Union


PYTHON_TO_XSD_TYPES: Dict[Type, str] = {
    int: "xsd:integer",
    float: "xsd:float",
    str: "xsd:string",
    bool: "xsd:boolean",
    datetime.datetime: "xsd:dateTime",
    datetime.date: "xsd:date",
    datetime.time: "xsd:time",
}

STRING_TO_XSD_TYPES: Dict[str, str] = {
    "int": "xsd:integer",
    "float": "xsd:float",
    "str": "xsd:string",
    "bool": "xsd:boolean",
    "datetime": "xsd:dateTime",
    "date": "xsd:date",
    "time": "xsd:time",
}


def get_xsd_type(python_type: Union[Type, str]) -> str:
    """
    Get the XSD type for a Python type.
    
    :param python_type: The Python type to map (can be a type object or string)
    :return: The XSD type as a string
    """
    # Handle string type annotations
    if isinstance(python_type, str):
        return STRING_TO_XSD_TYPES.get(python_type, "xsd:string")
    
    # Handle type objects
    return PYTHON_TO_XSD_TYPES.get(python_type, "xsd:string")
