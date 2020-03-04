# Copyright (c) 2020 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
This module provides a set of functions that can be useful while
writing REST API servers.  It includes a decorator, #entrypoint.

# Decorators

#entrypoint marks functions as entrypoints.
"""

from typing import List, Optional


########################################################################
########################################################################

# decorators

DEFAULT_METHODS = {
    'list': ['GET'],
    'get': ['GET'],
    'update': ['PUT'],
    'create': ['POST'],
    'patch': ['PATCH'],
    'delete': ['DELETE'],
}

ATTR_NAME = 'entrypoint routes'


def entrypoint(path: str, methods: Optional[List[str]] = None):
    """Decorate a function so that it is exposed as an entrypoint.

    If the function it decorates does not have a 'standard' name,
    `methods` must be specified.

    `path` may contain _placeholders_, that will be mapped to function
    parameters at call time:

    ```python
    @entrypoint('/foo/{bar}/baz/{foobar}')
    def get(self, bar, foobar):
        pass

    @entrypoint('/foo1')
    @entrypoint('/foo2')
    def list():
        pass
    ```

    Possible values for strings in `methods` are: `'GET'`, `'POST'`,
    `'PUT'`, `'DELETE'`, `'OPTIONS'`, and `'PATCH'`.

    Decorated functions will have an `entrypoint routes` attribute
    added, which will contain a list of a dictionary with the following
    entries:

    - path: a non-empty string
    - methods: a list of strings

    The decorated functions are otherwise unmodified.

    There can be as many entrypoint decorators as required for a
    function.

    # Required parameters

    - path: a non-empty string

    # Optional parameters

    - methods: a list of strings or None.  (None by default)

    # Raised exceptions

    A _ValueError_ exception is raised if the wrapped function does not
    have a standard entrypoint name and `methods` is not specified.

    A _ValueError_ exception is raised if `methods` is specified and
    contains unexpected values (must be a standard HTTP verb).
    """

    def inner(f):
        _methods = DEFAULT_METHODS.get(f.__name__)
        if _methods is None and methods is None:
            raise ValueError(
                f"Nonstandard entrypoint '{f.__name__}', 'methods' parameter required."
            )
        setattr(
            f,
            ATTR_NAME,
            getattr(f, ATTR_NAME, [])
            + [{'path': path, 'methods': methods or _methods}],
        )
        return f

    return inner
