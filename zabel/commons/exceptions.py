# Copyright (c) 2019 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
This module provides an #ApiError class that is used by the **zabel**
packages to represent unexpected events occurring while calling the
underlying APIs.
"""

########################################################################
########################################################################

# errors wrapper


class ApiError(Exception):
    """The tooling API exception class."""
