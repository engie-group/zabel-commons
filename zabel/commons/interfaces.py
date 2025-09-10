# Copyright (c) 2019 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
**The deprecated Utility and ManagedService interfaces have been
removed.**

This module provides two interfaces that are used to manage API
services:

| Interfaces           {.s} | Description                              |
| ------------------------- | ---------------------------------------- |
| #ApiServer                | A marker for API servers.                |
| #Image                    | A marker for images (containers-like API
                              services).                               |
"""


from .kludgeutility import KludgeManager as Manager, KludgeUtility as Utility


########################################################################
## Interfaces


class ApiServer:
    """An API server marker."""


class Image:
    """Abstract Image Wrapper.

    Provides a minimal set of features an image must provide:

    - constructor (`__init__`)
    - a `run()` method

    Implementing classes must have a constructor with the following
    signature:

    ```python
    def __init__(self):
    ```

    The `run()` method takes any number of parameters.  It represents
    the image activity.
    """
