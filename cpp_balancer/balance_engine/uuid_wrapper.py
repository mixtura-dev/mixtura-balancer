"""
UUID conversion utilities for balance_engine module.

Converts between Python's uuid.UUID objects and integers,
which are used internally by the C++ balance engine.
"""

import uuid as python_uuid
from typing import Union


def uuid_to_int(py_uuid: Union[python_uuid.UUID, str]) -> int:
    """
    Convert Python UUID to integer.
    
    Args:
        py_uuid: A Python uuid.UUID object or UUID string
        
    Returns:
        Integer hash of the UUID
        
    Raises:
        TypeError: If the input cannot be converted to UUID
        ValueError: If the UUID string is invalid
    """
    if isinstance(py_uuid, str):
        py_uuid = python_uuid.UUID(py_uuid)
    elif not isinstance(py_uuid, python_uuid.UUID):
        raise TypeError(f"Expected UUID or str, got {type(py_uuid)}")
    
    # Convert UUID bytes to integer (use first 8 bytes)
    return int.from_bytes(py_uuid.bytes[:8], byteorder='big')


def int_to_uuid(int_val: int) -> python_uuid.UUID:
    """
    Convert integer back to a UUID-like representation.
    
    Note: This creates a UUID by padding the integer.
    The mapping is not reversible for all UUIDs, but works 
    for the purpose of identifying roles within this session.
    
    Args:
        int_val: Integer value
        
    Returns:
        Python uuid.UUID object
    """
    # Pad integer to 16 bytes
    bytes_val = int_val.to_bytes(8, byteorder='big') + b'\x00' * 8
    return python_uuid.UUID(bytes=bytes_val)


def python_to_cpp(py_uuid: Union[python_uuid.UUID, str]) -> int:
    """
    Convert Python UUID to C++ int representation.
    
    Args:
        py_uuid: A Python uuid.UUID object or UUID string
        
    Returns:
        Integer for use in C++
    """
    return uuid_to_int(py_uuid)


def cpp_to_python(cpp_int: int) -> python_uuid.UUID:
    """
    Convert C++ int representation back to Python UUID.
    
    Args:
        cpp_int: Integer from C++
        
    Returns:
        Python uuid.UUID object
    """
    return int_to_uuid(cpp_int)


def python_uuid_list_to_cpp(py_uuids: list[python_uuid.UUID]) -> list[int]:
    """
    Convert a list of Python UUIDs to a list of C++ ints.
    
    Args:
        py_uuids: List of Python UUID objects
        
    Returns:
        List of integers for use in C++
    """
    return [python_to_cpp(uid) for uid in py_uuids]


def cpp_uuid_list_to_python(cpp_ints: list[int]) -> list[python_uuid.UUID]:
    """
    Convert a list of C++ ints back to Python UUIDs.
    
    Args:
        cpp_ints: List of integers from C++
        
    Returns:
        List of Python UUID objects
    """
    return [cpp_to_python(i) for i in cpp_ints]


class UUIDConverter:
    """
    Utility class for UUID conversions.
    
    Provides convenient methods for batch conversions.
    """
    
    @staticmethod
    def to_int(py_uuid: Union[python_uuid.UUID, str]) -> int:
        """Convert UUID to int."""
        return python_to_cpp(py_uuid)
    
    @staticmethod
    def to_uuid(cpp_int: int) -> python_uuid.UUID:
        """Convert int to UUID."""
        return cpp_to_python(cpp_int)
    
    @staticmethod
    def to_ints(py_uuids: list[python_uuid.UUID]) -> list[int]:
        """Convert list of UUIDs to ints."""
        return python_uuid_list_to_cpp(py_uuids)
    
    @staticmethod
    def to_uuids(cpp_ints: list[int]) -> list[python_uuid.UUID]:
        """Convert list of ints to UUIDs."""
        return cpp_uuid_list_to_python(cpp_ints)


__all__ = [
    "python_to_cpp",
    "cpp_to_python",
    "python_uuid_list_to_cpp",
    "cpp_uuid_list_to_python",
    "UUIDConverter",
]
