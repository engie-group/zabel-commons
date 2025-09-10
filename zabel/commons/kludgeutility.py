# Copyright (c) 2020 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
A kludge to allow for a safe 1.8 release.
"""

from typing import Any, Callable, Dict, List, Tuple

import json

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


def _read_server_params(args, host, port):
    host = args[args.index('--host') + 1] if '--host' in args else host
    port = int(args[args.index('--port') + 1]) if '--port' in args else port
    return host, port


class KludgeUtility:
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


class KludgeManager:
    """Abstract Manager Wrapper.

    A simple marker for manager classes.

    # Properties

    | Property name | Description          | Default implementation? |
    | ------------- | -------------------- | ----------------------- |
    | `platform`    | The platform the
                      manager is part of.  | Yes (read/write)        |
    """

    _platform: Any

    @property
    def platform(self) -> Any:
        """Return the Platform the manager is attached to."""
        return self._platform

    @platform.setter
    def platform(self, value: Any) -> None:
        """Set the Platform the manager is attached to."""
        # pylint: disable=attribute-defined-outside-init
        self._platform = value
