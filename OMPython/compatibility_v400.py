# -*- coding: utf-8 -*-
"""
Helper functions for compatibility with OMPython v4.0.0
"""
import warnings
from typing import Optional


def depreciated_class(msg: Optional[str] = None):
    """
    Decorator for depreciated / compatibility classes.
    """

    def depreciated(cls):
        """
        Helper functions to do the decoration part.
        """

        class Wrapper(cls):
            """
            Wrapper to define the depreciation message.
            """

            def __init__(self, *args, **kwargs):
                message = f"The class {cls.__name__} is depreciated and will be removed in future versions!"
                if msg is not None:
                    message += f" {msg}"

                warnings.warn(
                    message=message,
                    category=DeprecationWarning,
                    stacklevel=3,
                )

                super().__init__(*args, **kwargs)

        return Wrapper

    return depreciated
