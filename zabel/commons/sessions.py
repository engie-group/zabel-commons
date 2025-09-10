# Copyright (c) 2019 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
This module provides a set of functions that can be useful while
making HTTP(S) requests.  It includes a factory function,
#prepare_session() and a class, #PersistentSession.

It depends on the public **requests** library.

## Factory Function

The #prepare_session() function returns a new #PersistentSession
instance.

## Class

The #PersistentSession class is a callable that returns a
`requests.Session` object.  The session is created only when the
callable is called for the first time.

## Usage

```python
from zabel.commons.sessions import prepare_session

session = prepare_session(auth='token')
# The HTTP session doesn't exist yet.
session().get('http://example.com/foo')
# The HTTP session is now open
session().put('http://example.com/foo', data='bar')
# The same HTTP session was used, and the session is still open
```
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
    """
    return PersistentSession(auth, cookies, verify)
