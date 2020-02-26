# Copyright (c) 2019 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
This module provides a _Credentials_ class that can be used to manage
credentials.
"""

from typing import Any, Dict, Optional, Union

import json


########################################################################
########################################################################

## credentials management


def _merge(
    source: Dict[str, Any], destination: Dict[str, Any]
) -> Dict[str, Any]:
    """Deep-merge two dictionaries.

    # Required parameters

    - `source`: a dictionary
    - `destination`: a dictionary

    Overwrites entries in `destination` with values in `source`.  In
    other words, `source` is a sparse dictionary, and its entries will
    overwrite existing ones in `destination`.  Entries in `destination`
    that are not in source will be preserved as-is.

    # Returned value

    The merged dictionary.

    ```python
    >>> a = {'first': {'all_rows': {'pass': 'dog', 'number': '1'}}}
    >>> b = {'first': {'all_rows': {'fail': 'cat', 'number': '5'}}}
    >>> merge(b, a) == {'first': {'all_rows': {'pass': 'dog',
    >>>                                        'fail': 'cat',
    >>>                                        'number': '5'}}}
    ```
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            _merge(value, node)
        else:
            destination[key] = value

    return destination


class Credentials:
    """Provide a simple interface to credentials."""

    @classmethod
    def from_str(cls, string: str) -> 'Credentials':
        """Create a Credentials object from a string (class method).

        # Required parameters

        - `string (str)`: a valid JSON structure

        # Returned value

        A _Credentials_ object whose content corresponds to `string`.
        """
        return cls(json.loads(string))

    def __init__(self, source: Union[str, Dict[str, Any]]) -> None:
        """Create a Credentials object.

        # Required parameters

        - `source`: a string or a dictionary.

        If `source` is a string, it is either a file name or any other
        resource name that support the open/read protocol.

        Credentials will be read from this resource, which is expected
        to be a JSON structure containing a dictionary with dictionaries
        as values:

        ```python
        {
            'foo': {
                'xyzzy1': ...,
                'xyzzy2': ...
            },
            'bar': {
                'abcde1': ...
            }
        }
        ```

        If `source` is a dictionary, it is expected to follow the same
        format and will be used as-is.
        """
        self.base: Optional[str] = None
        self.credentials_cache: Optional[Dict[str, Any]] = None
        if isinstance(source, dict):
            self.credentials_cache = source
            self.base = json.dumps(source)
            source = '<from dict>'
        self.source = source
        self.impersonation = None

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.source}'

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: {self.source}>'

    def get(self, tool: str, item: str) -> Optional[Any]:
        """Return the requested credential.

        # Required parameters

        - `tool (str)`: the name of the top-level key
        - `item (str)`: the name of the secondary-level key

        # Returned value

        None if the `tool` or `item` keys are not found, the value
        otherwise.
        """
        if self.credentials_cache is None:
            with open(self.source) as crd:
                self.credentials_cache = json.load(crd)
            if self.impersonation is not None:
                self.credentials_cache = _merge(
                    self.impersonation, self.credentials_cache
                )

        try:
            return self.credentials_cache[tool][item]
        except KeyError:
            return None

    def contains(self, tool: str) -> bool:
        """Returns True if credentials are defined for tool .

        # Required parameters

        - tool: a string

        # Returned value

        A boolean.  True if there are entries for `tool`, False
        otherwise.
        """
        if self.credentials_cache is None:
            if self.base:
                self.credentials_cache = json.loads(self.base)
            else:
                with open(self.source) as crd:
                    self.credentials_cache = json.load(crd)
                self.base = json.dumps(self.credentials_cache)
            if self.impersonation is not None:
                self.credentials_cache = _merge(
                    self.impersonation, self.credentials_cache
                )

        try:
            return tool in self.credentials_cache
        except KeyError:
            return False

    def impersonate(self, user: Optional[str]) -> 'Credentials':
        """Impersonate user.

        Impersonation means acting as user.

        User credentials will be read from this resource, which is
        expected to be a JSON structure containing a dictionary of
        dictionaries.

        The user structure is expected to match the credentials
        structure, with possible holes (which means the initial
        credentials values for those holes will be preserved).

        # Required parameters

        - `user (str or None)`: a file name or any other resource name
            that support the open/read protocol or None.

        If `user` is None, the credentials object will stop
        impersonating another user.

        # Returned Value

        self.
        """
        if user is None:
            self.impersonation = self.credentials_cache = None
        else:
            with open(user, 'r') as overlay:
                self.impersonation = json.load(overlay)
                self.credentials_cache = None

        return self
