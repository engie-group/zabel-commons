# Copyright (c) 2020 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
This module provides a set of functions that can be useful while
writing REST API servers.  It includes a decorator, #entrypoint, as
well as a set of helpers: #make_status and #make_items.

It also provides some commonly-used references, `DEFAULT_HEADERS` and
`REASON_STATUS`.

# Decorators

#entrypoint marks functions as entrypoints.
"""

from typing import Any, Dict, List, Optional, Union


########################################################################
########################################################################

# Security Headers

DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Strict-Transport-Security': 'max-aincludeSubDomains',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'no-referrer',
    'Content-Security-Policy': 'default-src \'none\'',
}


# API Server Helpers

REASON_STATUS = {
    'OK': 200,
    'Created': 201,
    'NoContent': 204,
    'BadRequest': 400,
    'Unauthorized': 401,
    'PaymentRequired': 402,
    'Forbidden': 403,
    'NotFound': 404,
    'AlreadyExists': 409,
    'Conflict': 409,
    'Invalid': 422,
}


def make_status(
    reason: str, message: str, details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Return a new status object.

    # Required parameters

    - reason: a non-empty string (must exist in `REASON_STATUS`)
    - message: a string

    # Optional parameters:

    - details: a dictinnary or None (None by default)

    # Returned value

    A _status_.  A status is a dictionary with the following entries:

    - kind: a string (`'Status'`)
    - apiVersion: a string (`'v1'`)
    - metadata: an empty dictionary
    - status: a string (either `'Success'` or `'Failure'`)
    - message: a string (`message`)
    - reason: a string (`reason`)
    - details: a dictionary or None (`details`)
    - code: an integer (derived from `reason`)
    """
    code = REASON_STATUS[reason]
    return {
        'kind': 'Status',
        'apiVersion': 'v1',
        'metadata': {},
        'status': 'Success' if code // 100 == 2 else 'Failure',
        'message': message,
        'reason': reason,
        'details': details,
        'code': code,
    }


def make_items(kind: str, what: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return list object.

    # Required parameters

    - kind: a non-empty string
    - what: a list of dictionaries

    # Returned value

    A _list_.  A list is a dictionary with the following entries:

    - kind: a string
    - apiVersion: a string (`'v1'`)
    - items: a list of dictionaries (`what`)
    """
    return {'apiVersion': 'v1', 'kind': f'{kind}List', 'items': what}


# Decorators

DEFAULT_METHODS = {
    'list': ['GET'],
    'get': ['GET'],
    'create': ['POST'],
    'update': ['PUT'],
    'delete': ['DELETE'],
    'patch': ['PATCH'],
}

ATTR_NAME = 'entrypoint routes'


def entrypoint(
    path: Union[str, List[str]],
    methods: Optional[List[str]] = None,
    rbac: bool = True,
):
    """Decorate a function so that it is exposed as an entrypoint.

    If the function it decorates does not have a 'standard' name,
    or if its name does not start with a 'standard' prefix, `methods`
    must be specified.

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

    @entrypoint(['/bar', '/baz'])
    def list():
        pass
    ```

    Possible values for strings in `methods` are: `'GET'`, `'POST'`,
    `'PUT'`, `'DELETE'`, `'PATCH'`, and `'OPTIONS'`.

    The corresponding 'standard' names are `'list'` and `'get'`,
    `'create'`, `'update'`, `'delete'`, and `'patch'`.  There is no
    'standard' name for the `'OPTIONS'` method.

    'Standard' prefixes are standard names followed by `'_'`, such
    as `'list_foo'`.

    Decorated functions will have an `entrypoint routes` attribute
    added, which will contain a list of a dictionary with the following
    entries:

    - path: a non-empty string or a list of non-empty strings
    - methods: a list of strings
    - rbac: a boolean

    The decorated functions are otherwise unmodified.

    There can be as many entrypoint decorators as required for a
    function.

    # Required parameters

    - path: a non-empty string or a list of non-empty strings

    # Optional parameters

    - methods: a list of strings or None (None by default).
    - rbac: a boolean (True by default).

    # Raised exceptions

    A _ValueError_ exception is raised if the wrapped function does not
    have a standard entrypoint name and `methods` is not specified.

    A _ValueError_ exception is raised if `methods` is specified and
    contains unexpected values (must be a standard HTTP verb).
    """

    def inner(f):
        for prefix, words in DEFAULT_METHODS.items():
            if f.__name__ == prefix or f.__name__.startswith(f'{prefix}_'):
                _methods = words
                break
        else:
            _methods = None
        if _methods is None and methods is None:
            raise ValueError(
                f"Nonstandard entrypoint '{f.__name__}', 'methods' parameter required."
            )
        setattr(
            f,
            ATTR_NAME,
            getattr(f, ATTR_NAME, [])
            + [
                {'path': p, 'methods': methods or _methods, 'rbac': rbac}
                for p in paths
            ],
        )
        return f

    paths = [path] if isinstance(path, str) else path
    return inner
