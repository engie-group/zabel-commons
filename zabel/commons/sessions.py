# Copyright (c) 2019 Martin Lafaix (rv5617@engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
This module provides a set of functions that can be useful while
making HTTP(S) requests.  It includes a class, #PersistentSession,
as well as a factory method, #prepare_session().

It depends on the public **requests** library.

Sessions are `requests.Session` objects.  They can be closed either
implicitly (`with session(): ...`) or explicitly (`session().close()`).
If so, they will reopen as needed.
"""

from typing import Any, Dict, Optional

import requests
from requests.utils import cookiejar_from_dict


class PersistentSession:
    """Persistent Sessions

    Persistent sessions are not opened at initialization time.

    They must be called at least once to open.
    """

    def __init__(
        self,
        auth: Any,
        cookies: Optional[Dict[str, str]] = None,
        verify: bool = True,
    ) -> None:
        """Initialize a new requests.Session object.

        # Required parameters

        - auth: an object

        # Optional parameters

        - cookies: a dictionary or None (None by default)
        - verify: a boolean (True by default)
        """
        self.auth = auth
        self.cookies = cookies
        self.verify = verify
        self.session: Optional[requests.Session] = None

    def __call__(self) -> requests.Session:
        if self.session is None:
            self.session = requests.Session()
            self.session.auth = self.auth
            if self.cookies:
                self.session.cookies = cookiejar_from_dict(
                    self.cookies, self.session.cookies
                )
            self.session.verify = self.verify
        return self.session


def prepare_session(
    auth: Any, cookies: Optional[Dict[str, str]] = None, verify: bool = True
) -> PersistentSession:
    """Return a new Persistent Session object.

    # Required parameters

    - auth: an object

    # Optional parameters

    - cookies: a dictionary or None (None by default)
    - verify: a boolean (True by default)

    # Returned value

    A new #PersistentSession instance.

    # Sample usage

    ```python
    >>> from commons.sessions import prepare_session
    >>>
    >>> session = prepare_session('token')
    >>> # The HTTP session doesn't exist yet.
    >>> session().get('http://example.com/foo')
    >>> # The HTTP session is now open
    >>> session().put('http://example.com/foo', data='bar')
    >>> # The same HTTP session was used
    ```
    """
    return PersistentSession(auth, cookies, verify)
