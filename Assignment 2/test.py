import os
import sys
from math import pi, sqrt

class ExampleClass:
    """This is an example class with a docstring."""

    def __init__(self, value: int):
        """Initialize with a value."""
        self.value = value

    def multiply(self, factor: int) -> int:
        """Multiply value by a factor."""
        return self.value * factor

    def no_annotation_method(self):
        pass


def standalone_function(x: float) -> float:
    """Calculate the square root of x."""
    return sqrt(x)

def another_function_without_annotation():
    pass
