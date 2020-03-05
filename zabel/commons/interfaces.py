# Copyright (c) 2019 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
This module provides eight interfaces that are used to manage services:

| Interfaces                | Description                              |
| ------------------------- | ---------------------------------------- |
| #Controller               | Defines methods all controllers must
                              implement.                               |
| #Api                      | Defines methods all APIs must implement. |
| #ManagedProjectDefinition | An abstract class that represents a
                              minimal managed project definition.      |
| #ManagedAccount           | An abstract class that represents a
                              minimal managed account.                 |
| #Manager                  | A simple marker for manager classes.     |
| #Service                  | Defines a handful of methods all
                              services must implement.                 |
| #Utility                  | Extends #Service and is implemented by
                              the shared services (services that are
                              used by multiple platforms or realms)    |
| #ManagedService           | Extends #Service and is implemented by
                              the abstract classes wrapping each tool.
                              It defines the methods all managed
                              services must implement (those relative
                              to being a #Service and those relative
                              to having members and pushing and
                              pulling projects).                       |
"""


from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)

import re

from .exceptions import ApiError
from .utils import api_call


########################################################################
## Constants

KEY = r'[a-z0-9A-Z-_.]+'
VALUE = r'[a-z0-9A-Z-_.]+'
EQUAL_EXPR = rf'^({KEY})\s*([=!]?=)\s*({VALUE})$'
SET_EXPR = rf'^({KEY})\s+(in|notin)\s+\(({VALUE}(\s*,\s*{VALUE})*)\)$'
EXISTS_EXPR = rf'^{KEY}$'


########################################################################
## Interfaces


class Controller:
    """Abstract Controller Wrapper."""


class Api:
    """Abstract Api Wrapper."""

    def list(
        self, kind: str, namespace: Optional[str] = None, **kwargs: Any
    ) -> List[Any]:
        """Return list of objects of specified kind."""
        raise NotImplementedError

    def get(
        self,
        kind: str,
        name: str,
        namespace: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Get an object."""
        raise NotImplementedError

    def delete(
        self,
        kind: str,
        name: str,
        namespace: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Delete object."""
        raise NotImplementedError

    def create(
        self,
        body: Dict[str, Any],
        namespace: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Create object from manifest."""
        raise NotImplementedError

    def update(
        self,
        kind: str,
        name: str,
        body: Dict[str, Any],
        namespace: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Update object from manifest."""
        raise NotImplementedError

    def patch(
        self,
        kind: str,
        name: str,
        body: Dict[str, Any],
        namespace: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Patch object from manifest."""
        raise NotImplementedError


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
    def from_dict(cls, dic: Dict[str, Any]) -> 'ManagedAccount':
        """Convert a dictionary to a _ManagedAccount_ object.

        # Required parameters

        - dic: a dictionary

        Should a platform implementation provide its own wrapper, it
        will most likely have to override this class method.
        """
        definition = cls()
        for key in dic:
            definition[key] = dic[key]
        return definition


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


class Service:
    """Abstract Service Wrapper.

    Provides a minimal set of features a service must provide.

    - constructor (`__init__`)
    - accessors for name and platform

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
    | #match_selector()         | Yes                     |

    Unimplemented features will raise a _NotImplementedError_ exception.

    Some features provide default implementation, but those default
    implementations may not be very efficient.

    In addition to the included methods, implementing classes must also
    have a constructor with the following signature:

    ```python
    def __init__(self, name, definition, credentials):
        ...
    ```

    Where `name` is a string (the name of the service on the platform),
    `definition` is a dictionary (tool-specific), and `credentials` is a
    #::Credentials object (or some object implementing its interface).

    The `definition` dictionary contains at least the following entry:

    - `type (class)`: a class object

    It may contain additional entries, such as `url` (a string), but
    this is service-dependent.

    Those entries are typically set in the platform definition.
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

    def match_selector(self, selector: str) -> bool:
        """Return True if the service match the selector.

        An empty selector always match.

        Currently, a subset of what should be done has been implemented:

            expr[,expr]*

        where `expr` is one of `key`, `!key`, or `key op value`, with
        `op` being one of `=`, `==`, or `!=`.

        The `in` and `notin` set-based requirements have yet to be
        implemented.

        # Required parameters

        - selector: a string

        # Returned value

        A boolean.
        """
        labels: Dict[str, str] = self.metadata.get('labels', {})

        def _evaluate(req: str) -> bool:
            if req == '':
                return True
            if re.match(EXISTS_EXPR, req):
                return req in labels
            if req[0] == '!' and re.match(EXISTS_EXPR, req[1:]):
                return req[1:] not in labels
            expr = re.match(EQUAL_EXPR, req)
            if expr is None:
                raise ValueError(f'Invalid expression {expr}.')
            key, ope, value = expr.groups()
            if key in labels:
                if ope in ('=', '=='):
                    return labels[key] == value
                return labels[key] != value
            return ope == '!='

        return all(_evaluate(sel.strip()) for sel in selector.split(','))


class Utility(Service):
    """Abstract Shared Service Wrapper.

    This class extends #Service and is abstract.  It declares a minimal
    set of features a utility (a shared service) must provide, in
    addition to the #Service ones.
    """


class ManagedService(Service):
    """Abstract Managed Service Wrapper.

    This class extends #Service and is abstract.  It declares a minimal
    set of features a managed service must provide, in addition to
    the #Service ones:

    - canonical user names management
    - members getters
    - project push and pull

    # Added Methods

    | Method name                | Default implementation? |
    | -------------------------- | ------------------------|
    | #get_canonical_member_id() | No                      |
    | #get_internal_member_id()  | No                      |
    | #list_members()            | No                      |
    | #get_member()              | No                      |
    | #push_project()            | No                      |
    | #push_users()              | No                      |
    | #pull_project()            | No                      |
    | #pull_users()              | No                      |

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

    @api_call
    def list_members(self) -> Dict[str, Any]:
        """Return the members on the service.

        # Returned values

        A dictionary.  The keys are the canonical IDs and the values are
        the representations of a user for the service.
        """
        raise NotImplementedError

    @api_call
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

    @api_call
    def push_project(self, project: ManagedProjectDefinition) -> None:
        """Push (aka publish) managed project on service.

        Members defined for the project are not pushed on service.  Use
        #push_users() for that purpose.

        # Required parameters

        - project: a managed project definition

        # Raised exceptions

        Raises an exception if the managed project is not successfully
        pushed.
        """
        raise NotImplementedError

    @api_call
    def push_users(self, project: ManagedProjectDefinition) -> None:
        """Push (aka publish) managed project users on service.

        It assumes the project has been previously successfully pushed.
        It may fail otherwise.

        # Required parameters

        - project: a managed project definition

        It assumes the project has been previously successfully pushed
        on the service.

        # Raised exception

        Raises an exception if the managed project users are not
        successfully pushed.
        """
        raise NotImplementedError

    @api_call
    def pull_project(self, project: ManagedProjectDefinition) -> Any:
        """Pull (aka extract) managed project users on service.

        # Required parameters

        - project: a managed project definition
        """
        raise NotImplementedError

    @api_call
    def pull_users(self, project: ManagedProjectDefinition) -> Any:
        """Pull (aka extract) managed project definition on service.

        # Required parameters

        - project: a managed project definition
        """
        raise NotImplementedError
