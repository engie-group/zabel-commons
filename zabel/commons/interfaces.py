# Copyright (c) 2019 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
This module provides nine interfaces that are used to manage services:

| Interfaces                | Description                              |
| ------------------------- | ---------------------------------------- |
| #ApiService               | Defines methods all ApiServices must
                              implement.                               |
| #Controller               | Defines methods all controllers must
                              implement.                               |
| #Image                    | Defines methods all images must
                              implement.                               |
| #Manager                  | A simple marker for manager classes.     |
| #ManagedProjectDefinition | An abstract class that represents a
                              minimal managed project definition.      |
| #ManagedAccount           | An abstract class that represents a
                              minimal managed account.                 |
| #BaseService              | Defines a handful of methods all
                              services must implement.                 |
| #ManagedService           | Extends #BaseService and is implemented
                              by the abstract classes wrapping each
                              tool.  It defines the methods all managed
                              services must implement (those relative
                              to being an #BaseService and those
                              relative to having members and pushing
                              and pulling projects).                   |
| #Utility                  | Extends #BaseService and is implemented
                              by the shared services (services that are
                              used by multiple platforms or realms)    |
"""


from typing import Any, Dict, Union

import json

from .exceptions import ApiError
from .servers import entrypoint, DEFAULT_HEADERS


########################################################################
## Constants

KEY = r'[a-z0-9A-Z-_.]+'
VALUE = r'[a-z0-9A-Z-_.]+'
EQUAL_EXPR = rf'^({KEY})\s*([=!]?=)\s*({VALUE})$'
SET_EXPR = rf'^({KEY})\s+(in|notin)\s+\(({VALUE}(\s*,\s*{VALUE})*)\)$'
EXISTS_EXPR = rf'^{KEY}$'


########################################################################
## Interfaces


## Fabric


class ApiService:
    """Abstract Api Service Wrapper."""


class Controller:
    """Abstract Controller Wrapper."""


class Image:
    """Abstract Image Wrapper.

    Provides a minimal set of features an image must provide:

    - constructor (`__init__`)
    - a `run()` method

    Implementing classes must have a constructor with the following
    signature:

    ```python
    def __init__(self):
        ...
    ```

    The `run()` method takes any number of parameters.  It represents
    the image activity.
    """


## Core


class Manager:
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


class ManagedProjectDefinition(Dict[str, Any]):
    """Managed Project Definition.

    Provides a simple wrapper for _managed projects definitions_.

    Managed projects definitions are JSON files (handled as dictionaries
    in Python).

    The _ManagedProjectDefinition_ helper class inherits from `dict`,
    and provides a single class method, `from_dict()`.
    """

    @classmethod
    def from_dict(cls, source: Dict[str, Any]) -> 'ManagedProjectDefinition':
        """Convert a dictionary to a _ManagedProjectDefinition_ object.

        # Required parameters

        - source: a dictionary

        Should a platform implementation provide its own wrapper, it
        will most likely have to override this class method.
        """
        definition = cls()
        for key in source:
            definition[key] = source[key]
        return definition


class ManagedAccount(Dict[str, Any]):
    """Managed Account.

    Provides a simple wrapper for _managed accounts_.

    Managed accounts are object describing realm accounts (users,
    technical users, readers, admins, ...).

    Realm implementations may decide to provide their own wrapper, to
    help manage managed accounts.

    A managed account is attached to a realm.

    The _ManagedAccount_ helper class inherits from dict, and provides a
    single class method, `from_dict()`.
    """

    @classmethod
    def from_dict(cls, source: Dict[str, Any]) -> 'ManagedAccount':
        """Convert a dictionary to a _ManagedAccount_ object.

        # Required parameters

        - source: a dictionary

        Should a platform implementation provide its own wrapper, it
        will most likely have to override this class method.
        """
        definition = cls()
        for key in source:
            definition[key] = source[key]
        return definition


def _read_server_params(args, host, port):
    host = args[args.index('--host') + 1] if '--host' in args else host
    port = int(args[args.index('--port') + 1]) if '--port' in args else port
    return host, port


class BaseService(Image):
    """Abstract Service Wrapper.

    Provides a minimal set of features a service must provide.

    - accessors for name and platform

    _BaseService_ instances are expected to expose some entrypoints and
    make them available through a web server.

    This class provides a default implementation of such a server and
    exposes the defined entrypoints.

    Its `run()` that takes any number of string arguments.  It starts a
    web server on the host and port provided via `--host` and `--port`
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

    The exposed entrypoints are those defined on all instance members.
    The entrypoint definitions are inherited (i.e., you don't have to
    redefine them if they are already defined).

    ```python
    class Foo(BasicService):
        @entrypoint('/foo/bar')
        def get_bar():
            ...

    class FooBar(Foo):
        def get_bar():
            return 'foobar.get_bar'

    FooBar().run()  # curl localhost:8080/foo/bar -> foobar.get_bar
    ```

    **Note**: You can redefine the entrypoint attached to a method.
    Simply add a new `@entrypoint` decorator to the method.  And, if
    you want to disable the entrypoint, use `[]` as the path.

    **Note**: The web server is implemented using Bottle.  If you prefer
    or need to use another wsgi server, simple override the `run()`
    method in your class.  Your class will then have no dependency on
    Bottle.

    # Properties

    | Property name | Description          | Default implementation? |
    | ------------- | -------------------- | ----------------------- |
    | `metadata`    | The service metadata
                      (a dictionary).      | Yes (read/write)        |
    | `name`        | The service name.    | Yes (read/write)        |
    | `platform`    | The platform the
                      service is part of.  | Yes (read/write)        |

    # Declared Methods

    | Method name               | Default implementation? |
    | ------------------------- | ----------------------- |
    | #ensure_authn()           | No                      |
    | #run()                    | Yes                     |

    Unimplemented features will raise a _NotImplementedError_ exception.

    Some features provide default implementation, but those default
    implementations may not be very efficient.
    """

    _metadata: Dict[str, Any]

    @property
    def metadata(self) -> Any:
        """Return the service metadata."""
        return self._metadata

    @metadata.setter
    def metadata(self, value: Dict[str, Any]) -> None:
        """Set the service metadata."""
        self._metadata = value

    @property
    def name(self) -> str:
        """Return the service name.

        This value is defined in the platform definition.

        On a platform, all services have a unique name, so this may be
        used to disambiguate services of the same type in logging
        functions.

        # Returned value

        A string.

        # Raised exceptions

        An _ApiError_ exception is raised if the service does not have
        a name.
        """
        result = self.metadata.get('name')
        if result is None:
            raise ApiError('No service_name defined.')
        return result  # type: ignore

    @name.setter
    def name(self, value: str) -> None:
        """Set the service name."""
        # pylint: disable=attribute-defined-outside-init
        self.metadata['name'] = value

    _platform: Any

    @property
    def platform(self) -> Any:
        """Return the platform the service is attached to."""
        return self._platform

    @platform.setter
    def platform(self, value: Any) -> None:
        """Set the platform the service is attached to."""
        # pylint: disable=attribute-defined-outside-init
        self._platform = value

    def ensure_authn(self):
        """..."""
        raise NotImplementedError

    def run(self, *args):
        """Start a bottle app for instance.

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
                        self.ensure_authn()
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
        self.request = request
        # pylint: disable=attribute-defined-outside-init
        self.app = Bottle()

        for name in dir(self):
            method = getattr(self, name, None)
            if method:
                # The 'entrypoint routes' attr may be on a super method
                sms = [getattr(c, name, None) for c in self.__class__.mro()]
                eps = [getattr(m, 'entrypoint routes', None) for m in sms]
                for route in next((routes for routes in eps if routes), []):
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


class Utility(BaseService):
    """Abstract Shared Service Wrapper.

    This class extends #BaseService and is abstract.  It declares a
    minimal set of features a utility (a shared service) must provide,
    in addition to the #BaseService ones.
    """


class ManagedService(BaseService):
    """Abstract Managed Service Wrapper.

    This class extends #BaseService and is abstract.  It declares a
    minimal set of features a managed service must provide, in addition
    to the #BaseService ones:

    - canonical user names management
    - members getters
    - project push and pull

    # Added Methods

    | Method name                | Default implementation? | Exposed? |
    | -------------------------- | ------------------------| -------- |
    | #get_canonical_member_id() | No                      | No       |
    | #get_internal_member_id()  | No                      | No       |
    | #list_members()            | No                      | Yes      |
    | #get_member()              | No                      | Yes      |
    | #push_project()            | No                      | Yes      |
    | #push_users()              | No                      | Yes      |
    | #pull_project()            | No                      | Yes      |
    | #pull_users()              | No                      | Yes      |

    Unimplemented features will raise a _NotImplementedError_
    exception.
    """

    def get_canonical_member_id(self, user: Any) -> str:
        """Return the canonical member ID.

        # Required parameters

        - user: a service-specific user representation

        `user` is the service internal user representation. It may be
        a service-specific object or class.

        # Returned value

        A string.
        """
        raise NotImplementedError

    def get_internal_member_id(self, member_id: str) -> Union[str, int]:
        """Return the internal name.

        # Required parameters

        - member_id: a string

        `member_id` is the canonical member ID.

        # Returned value

        A string or an integer, depending on the service internals.
        """
        raise NotImplementedError

    @entrypoint('/v1/members')
    def list_members(self) -> Dict[str, Any]:
        """Return the members on the service.

        # Returned values

        A dictionary.  The keys are the canonical IDs and the values are
        the representations of a user for the service.
        """
        raise NotImplementedError

    @entrypoint('/v1/members/{member_id}')
    def get_member(self, member_id: str) -> Any:
        """Return details on user.

        # Required parameters

        - member_id: a string

        `member_id` is the canonical member ID.

        # Returned value

        The representation of the user for the service, which is
        service-specific.
        """
        raise NotImplementedError

    @entrypoint('/v1/managedprojects/{project}', methods=['PUT'])
    def push_project(self, project: str) -> None:
        """Push (aka publish) managed project on service.

        Members defined for the project are not pushed on service.  Use
        #push_users() for that purpose.

        # Required parameters

        - project: a managed project definition name

        # Raised exceptions

        Raises an exception if the managed project is not successfully
        pushed.
        """
        raise NotImplementedError

    @entrypoint('/v1/managedprojects/{project}/members', methods=['PUT'])
    def push_users(self, project: str) -> None:
        """Push (aka publish) managed project users on service.

        It assumes the project has been previously successfully pushed.
        It may fail otherwise.

        # Required parameters

        - project: a managed project definition name

        It assumes the project has been previously successfully pushed
        on the service.

        # Raised exception

        Raises an exception if the managed project users are not
        successfully pushed.
        """
        raise NotImplementedError

    @entrypoint('/v1/managedprojects/{project}', methods=['GET'])
    def pull_project(self, project: str) -> Any:
        """Pull (aka extract) managed project users on service.

        # Required parameters

        - project: a managed project definition name
        """
        raise NotImplementedError

    @entrypoint('/v1/managedprojects/{project}/members', methods=['GET'])
    def pull_users(self, project: str) -> Any:
        """Pull (aka extract) managed project definition on service.

        # Required parameters

        - project: a managed project definition name
        """
        raise NotImplementedError
