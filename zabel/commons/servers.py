# Copyright (c) 2020 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
This module provides a set of functions that can be useful while
writing REST API servers.  It includes an abstract class, #ApiApp, a
decorator, #entrypoint(), as well as a set of helpers: #make_status()
and #make_items().

It also provides some commonly-used references, `DEFAULT_HEADERS` and
`REASON_STATUS`.

## Abstract Class

| Class        {.s} | Description                      |
| ----------------- | -------------------------------- |
| #ApiApp           | An abstract API server wrapper.  |

## Decorators

| Decorator    {.s} | Description                      |
| ----------------- | -------------------------------- |
| #entrypoint()     | Marks functions as entry points. |

## Misc. Helpers

| Function     {.s} | Description                      |
| ----------------- | -------------------------------- |
| #make_status()    | Returns a status object.         |
| #make_items()     | Returns a list of objects.       |

## References

| Name         {.s} | Description                      |
| ----------------- | -------------------------------- |
| `DEFAULT_HEADERS` | Common security headers.         |
| `REASON_STATUS`   | Common reason-to-status mapping. |
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import json

from .interfaces import ApiServer


########################################################################
########################################################################

# Security Headers

DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
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

    # Optional parameters

    - details: a dictionary or None (None by default)

    # Returned value

    A _status_.  A status is a dictionary with the following entries:

    - apiVersion: a string (`'v1'`)
    - kind: a string (`'Status'`)
    - metadata: an empty dictionary
    - status: a string (either `'Success'` or `'Failure'`)
    - message: a string (`message`)
    - reason: a string (`reason`)
    - details: a dictionary or None (`details`)
    - code: an integer (derived from `reason`)

    # Usage

    ```python
    make_status('NotFound', 'The requested resource does not exist')

    # {
    #   'apiVersion': 'v1',
    #   'kind': 'Status',
    #   'metadata': {},
    #   'status': 'Failure',
    #   'message': 'The requested resource does not exist',
    #   'reason': 'NotFound',
    #   'details': None,
    #   'code': 404
    # }
    ```
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

    - apiVersion: a string (`'v1'`)
    - kind: a string (`'{kind}List'`)
    - items: a list of dictionaries (`what`)

    # Usage

    ```python
    make_items(
      'Foo',
      [{'metadata': {'name': 'foo'}}, {'metadata': {'name': 'bar'}}]
    )

    # {
    #   'apiVersion': 'v1',
    #   'kind': 'FooList',
    #   'items': [
    #     {'metadata': {'name': 'foo'}},
    #     {'metadata': {'name': 'bar'}}
    #   ]
    # }
    ```
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
    """Decorate a function so that it is exposed as an entry point.

    # Required parameters

    - path: a non-empty string or a possibly empty list of non-empty
      strings

    # Optional parameters

    - methods: a list of strings or None (None by default).
    - rbac: a boolean (True by default).

    # Raised exceptions

    A _ValueError_ exception is raised if the wrapped function does not
    have a standard entry point name and `methods` is not specified.

    A _ValueError_ exception is raised if `methods` is specified and
    contains unexpected values (must be a standard HTTP verb).

    # Usage

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

    Decorated functions will have an `'entrypoint routes'` attribute
    added, which will contain a list of a dictionary with the following
    entries:

    - path: a non-empty string or a list of non-empty strings
    - methods: a list of strings
    - rbac: a boolean

    The decorated functions are otherwise unmodified.

    There can be as many entry point decorators as required for a
    function.
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
                f'Nonstandard entrypoint "{f.__name__}", "methods" parameter required.'
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


def _read_server_params(args, host, port):
    host = args[args.index('--host') + 1] if '--host' in args else host
    port = int(args[args.index('--port') + 1]) if '--port' in args else port
    return host, port


class ApiApp(ApiServer):
    """Abstract API Service Wrapper.

    Provides a minimal set of features an API app must provide.

    _ApiApp_ instances are expected to expose some entry points and
    make them available through a web server.

    This class provides a default implementation of such a server and
    exposes the defined entry points.

    It also provides two abstract methods to ensure that incoming
    requests are authenticated and authorized.  You do not have to
    implement authentication and authorization if your service does not
    require it.

    # Declared Methods

    | Method name          {.s} | Default implementation? |
    | ------------------------- | ----------------------- |
    | #ensure_authn()           | No                      |
    | #ensure_authz()           | No                      |
    | #run()                    | Yes                     |

    Unimplemented features raise a _NotImplementedError_ exception.

    The `run()` method takes any number of string arguments.  It starts
    a web server on the host and port provided via `--host` and `--port`
    arguments, or, if not specified, via the `host` and `port` instance
    attributes, or `localhost` on port 8080 if none of the above are
    available:

    ```python
    # Explicit host and port
    foo.run('--host', '0.0.0.0', '--port', '80')

    # Explicit host, default port (8080)
    foo.run('--host', '192.168.12.34')

    # Host specified for the object, default port (8080)
    foo.host = '10.0.0.1'
    foo.run()

    # Default host and port (localhost:8080)
    foo.run()
    ```

    The exposed entry points are those defined on all instance members.
    The entry point definitions are inherited (i.e., you don't have to
    redefine them if they are already defined).

    !!! tip
        The default web server is implemented using **Bottle**.  It
        may not be very efficient.  If you prefer or need to use another
        WSGI server, simple override the `run()` method in your class.
        Your class will then have no dependency on **Bottle**.

        Refer to #enumerate_routes() for a way to get the list of
        defined entry points.

    # Example

    ```python
    from zabel.commons.servers import ApiApp, entrypoint

    class Foo(ApiApp):
        @entrypoint('/foo/bar')
        def get_bar():
            return 'foo.get_bar'

    class FooBar(Foo):
        def get_bar():
            return 'foobar.get_bar'

    FooBar().run()  # curl localhost:8080/foo/bar -> 'foobar.get_bar'
    ```

    You can redefine the entry point attached to a method.  Simply add a
    new `@entry point` decorator to the method.  And, if you want to
    disable the entry point, use `[]` as the path.

    ```python
    class BarBaz(Foo):
        @entrypoint([])  # Disable the entry point
        def get_bar():
            return 'barbaz.get_bar'

    BarBaz().run()  # curl localhost:8080/foo/bar -> 404
    ```

    ```python
    class BarFoo(Foo):
        @entrypoint('/bar/foo')  # New entry point
        def get_bar():
            return 'barfoo.get_bar'

    BarFoo().run()  # curl localhost:8080/foo/bar -> 404
    BarFoo().run()  # curl localhost:8080/bar/foo -> 'barfoo.get_bar'
    ```
    """

    def ensure_authn(self) -> str:
        """Ensure the incoming request is authenticated.

        This method is abstract and should be implemented by the
        concrete service class.

        # Returned value

        A string, the subject identity.

        # Raised exceptions

        Raises a _ValueError_ exception if the incoming request is not
        authenticated.  The ValueError argument is expected to be a
        _status_ object with an `'Unauthorized'` reason.
        """
        raise NotImplementedError

    def ensure_authz(self, sub) -> None:
        """Ensure the incoming request is authorized.

        This method is abstract and should be implemented by the
        concrete  service class.

        # Required parameters

        - sub: a string, the subject identity

        # Raised exceptions

        Raises a _ValueError_ exception if the subject is not allowed
        to perform the operation.  The ValueError argument is expected
        to be a _status_ object with a `'Forbidden'` reason.
        """
        raise NotImplementedError

    def run(self, *args) -> Any:
        """Start a bottle app for instance.

        Routes that requires RBAC will call #ensure_authn()
        and #ensure_authz().

        # Optional parameters

        - *args: strings.  See class definition for more details.

        # Returned value

        If the server thread dies, returns the exception.  Does not
        return otherwise.
        """
        # pylint: disable=import-outside-toplevel
        from bottle import Bottle, request, response

        def wrap(handler, rbac: bool):
            def inner(*args, **kwargs):
                for header, value in DEFAULT_HEADERS.items():
                    response.headers[header] = value
                if rbac:
                    try:
                        self.ensure_authz(self.ensure_authn())
                    except ValueError as err:
                        resp = err.args[0]
                        response.status = resp['code']
                        return resp
                if request.json:
                    kwargs['body'] = request.json
                try:
                    result = json.dumps(handler(*args, **kwargs))
                    return result
                except ValueError as err:
                    resp = err.args[0]
                    response.status = resp['code']
                    return resp

            return inner

        if not hasattr(self, 'port'):
            # pylint: disable=attribute-defined-outside-init
            self.port = 8080
        if not hasattr(self, 'localhost'):
            # pylint: disable=attribute-defined-outside-init
            self.host = 'localhost'

        # pylint: disable=attribute-defined-outside-init
        self.app = Bottle()

        for method, route in self.enumerate_routes():
            self.app.route(
                path=route['path'].replace('{', '<').replace('}', '>'),
                method=route['methods'],
                callback=wrap(method, route['rbac']),
            )

        host, port = _read_server_params(args, host=self.host, port=self.port)
        try:
            self.app.run(host=host, port=port)
        except Exception as err:
            return err

    def enumerate_routes(self) -> List[Tuple[Callable, Dict[str, Any]]]:
        """Enumerate all routes defined on instance members.

        You can use this method to get a list of all entry points
        defined on the instance.  This could be handy when overriding
        the `run()` method to use another web server than the default
        one.

        # Returned value

        A list of tuples.  Each tuple contains:

        - the member (a callable)
        - the entry point definition (a dictionary with `path`,
          `methods`, and `rbac` entries)

        The list is ordered by member name.

        # Usage

        Assuming your web server provides a `route` method with the
        same signature as the one provided by **Bottle**, you could
        use this method as follows:

        ```python
        for method, route in self.enumerate_routes():
            self.app.route(
                path=route['path'].replace('{', '<').replace('}', '>'),
                method=route['methods'],
                callback=wrap(method, route['rbac']),
            )
        ```

        Here, `wrap()` is a decorator that process the incoming
        request, in a way similar to the one used in the default
        `run()` method.  You will have to adjust it for your web server:

        ```python
        def wrap(handler, rbac: bool):
            def inner(*args, **kwargs):
                for header, value in DEFAULT_HEADERS.items():
                    response.headers[header] = value
                if rbac:
                    try:
                        self.ensure_authz(self.ensure_authn())
                    except ValueError as err:
                        resp = err.args[0]
                        response.status = resp['code']
                        return resp
                try:
                    result = json.dumps(handler(*args, **kwargs))
                    return result
                except ValueError as err:
                    resp = err.args[0]
                    response.status = resp['code']
                    return resp

            return inner
        ```
        """
        routes = []
        for name in dir(self):
            if method := getattr(self, name, None):
                # The 'entrypoint routes' attr may be on a super method
                sms = [getattr(c, name, None) for c in self.__class__.mro()]
                eps = [getattr(m, 'entrypoint routes', None) for m in sms]
                for route in next((routes for routes in eps if routes), []):
                    routes.append((method, route))
        return routes
