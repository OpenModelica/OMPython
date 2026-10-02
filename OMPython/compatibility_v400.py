# -*- coding: utf-8 -*-
"""
Helper functions for compatibility with OMPython v4.0.0
"""
import warnings
from typing import Optional


def deprecated_class(msg: Optional[str] = None):
    """
    Decorator for deprecated / compatibility classes.
    """

    def deprecated(cls):
        """
        Helper functions to do the decoration part.
        """

        class Wrapper(cls):
            """
            Wrapper to define the deprecation message.
            """

            def __init__(self, *args, **kwargs):
                """Construct the deprecated class and emit a deprecation warning."""
                message = f"The class {cls.__name__} is deprecated and will be removed in future versions!"
                if msg is not None:
                    message += f" {msg}"

                warnings.warn(
                    message=message,
                    category=DeprecationWarning,
                    stacklevel=3,
                )

                super().__init__(*args, **kwargs)

        return Wrapper

    return deprecated
