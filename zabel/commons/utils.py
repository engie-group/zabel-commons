# Copyright (c) 2019 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
This module provides a set of functions that can be useful while
writing APIs wrappers.  It includes a decorator, #api_call, a handful
of XML helpers and misc. functions, and helpers for parameters validity
checking.

It depends on the public **requests** library.

# Decorators

#api_call wraps functions that call a remote API.

#api_client wraps methods of a class with the #api_call decorator.

# XML Helpers

#dict_to_xml() and #xml_to_dict().

# Parameters Validity Checkers

#ensure_instance(), #ensure_noneorinstance(), #ensure_nonemptystring(),
#ensure_noneornonemptystring(), #ensure_onlyone(), and #ensure_in().

# Misc. Helpers

#add_if_specified(), #patch(), and #join_url().
"""

from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Mapping,
    MutableMapping,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from functools import wraps

import inspect

import requests

from .exceptions import ApiError

__all__ = [
    'api_call',
    'xml_to_dict',
    'dict_to_xml',
    'add_if_specified',
    'join_url',
    'patch',
    'ensure_instance',
    'ensure_noneorinstance',
    'ensure_nonemptystring',
    'ensure_noneornonemptystring',
    'ensure_onlyone',
    'ensure_in',
]


########################################################################
########################################################################

# decorators

FuncT = TypeVar('FuncT', bound=Callable[..., Any])


def api_call(function: FuncT) -> FuncT:
    """Decorate function so that failed API calls raise _ApiError_.

    If `function` returns a _Response_ object, its JSON content
    (possibly None if empty) is returned if the status code is in the
    2xx range.  An _ApiError_ is raised otherwise.

    If `function` does not return a _Response_ object, its returned
    value is passed unchanged.

    _ApiError_ and _ValueError_ are not nested, but other exceptions
    raised by `function` will be wrapped in an _ApiError_ exception.

    # Sample use

    ```python
    @api_call
    def foo(self, a, b, c):
        return 42
    ```
    """

    @wraps(function)
    def _inner(*args: Any, **kwargs: Any) -> Any:
        try:
            response = function(*args, **kwargs)
            if isinstance(response, requests.Response):
                if response.status_code // 100 == 2:
                    return None if response.text == '' else response.json()
                raise ApiError(response.text)
            return response
        except ValueError:
            raise
        except ApiError:
            raise
        except Exception as err:
            raise ApiError(err) from None

    return _inner  # type: ignore


def api_client(cls):
    """Decorate class methods with api_call.

    Does not wraps class methods and static methods.
    """
    for name, val in vars(cls).items:
        if callable(val):
            setattr(cls, name, api_call(val))
    return cls


########################################################################
########################################################################

# XML helpers


def xml_to_dict(xml: Any) -> Dict[str, Any]:
    """Convert an XML document to a corresponding dictionary.

    !!! important
        There should be no `'element text'` tag in the XML document.
    """
    dct = {xml.tag: [xml_to_dict(x) for x in xml.getchildren()]}
    dct.update(('@%s' % key, val) for key, val in xml.attrib.items())
    dct['element text'] = xml.text
    return dct


def dict_to_xml(dct: Mapping[str, Any]) -> str:
    """Convert a dictionary to a corresponding XML string.

    `dct` should follow the conventions of #xml_to_dict(): attributes
    are prefixed with an `'@'` symbol, which will be removed in the
    generated string.

    KLUDGE: recreate an XML tree, and convert it to a string. Right now,
    it does not support CDATA.
    """
    tag = [k for k in dct if k != 'element text' and k[0] != '@'][0]
    return '\n<{tag}{attrs}>{body}{text}</{tag}>'.format(
        tag=tag,
        attrs=''.join(
            [' %s="%s"' % (k[1:], v) for k, v in dct.items() if k[0] == '@']
        ),
        body=''.join(dict_to_xml(dd) for dd in dct[tag]),
        text=(dct['element text'] or '') if 'element text' in dct else '',
    )


########################################################################
########################################################################

# private helpers


def patch(
    destination: Dict[str, Any], changes: Dict[str, Any]
) -> Dict[str, Any]:
    """Deep-merge two dictionaries.

    # Required parameters

    - `destination`: a dictionary
    - `changes`: a dictionary

    Overwrites entries in `destination` with values in `changes`.  In
    other words, `changes` is a sparse dictionary, and its entries will
    overwrite existing ones in `destination`.  Entries in `destination`
    that are not in `changes` will be preserved as-is.

    # Returned value

    The patched dictionary.

    ```python
    >>> a = {'first': {'all_rows': {'pass': 'dog', 'number': '1'}}}
    >>> b = {'first': {'all_rows': {'fail': 'cat', 'number': '5'}}}
    >>> patch(a, b) == {'first': {'all_rows': {'pass': 'dog',
    >>>                                        'fail': 'cat',
    >>>                                        'number': '5'}}}
    ```
    """
    for key, value in changes.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            patch(node, value)
        else:
            destination[key] = value

    return destination


def add_if_specified(
    dct: MutableMapping[str, Any], key: str, val: Any,
) -> None:
    """Add a key:value pair to dictionary if value is not None.

    # Required parameters

    - dct: a dictionary
    - key: a string
    - val: anything

    # Returned value

    None.
    """
    if val is not None:
        dct[key] = val


def join_url(lhs: str, rhs: str) -> str:
    """Join two parts to make an URL.

    It does not try to interpret the URL.  In particular, it differs
    from `urllib.path.urljoin` in that:

    ```python
    >>> join_url('https://example.com/foo', 'bar')
    'https://example.com/foo/bar'
    >>> urljoin('https://example.com/foo', 'bar')
    'https://example.com/bar'
    ```
    """
    return lhs.rstrip('/') + '/' + rhs.lstrip('/')


########################################################################
########################################################################

# parameters checks


def _isnoneorinstance(
    val: Optional[type], typ: Union[type, Tuple[type, ...]]
) -> bool:
    """Return True if val is either None or an instance of class typ.

    `typ` can be a type or a tupple of types.
    """
    return val is None or isinstance(val, typ)


def _isnonemptystring(val: Any) -> bool:
    """Return True if val is a non-empty string."""
    return isinstance(val, str) and len(val) > 0


def _isnoneornonemptystring(val: Any) -> bool:
    """Return True if val is either None or a non-empty string."""
    return val is None or _isnonemptystring(val)


def _getlocal(val: Optional[Any], name: str) -> Any:
    if val is None:
        raise SystemError('No previous frame, should not happen, aborting.')
    return val.f_back.f_locals[name]


# assertions


def _describe(typ: Union[type, Tuple[type, ...]]) -> str:
    """Return a human-friendly description of typ.

    `typ` may be a type or a tuple of types.
    """
    if isinstance(typ, tuple):
        return (', '.join(i.__name__ for i in typ[1:])) + (
            ', or %s' % typ[0].__name__
        )
    return typ.__name__


def ensure_instance(name: str, typ: Union[type, Tuple[type, ...]]) -> None:
    """Ensure name is an instance of typ.

    # Required parameters

    - name: a string, the name of the local variable to check
    - typ: a type or a tuple of types

    # Raised exceptions

    Raise _ValueError_ if the condition is not satisfied.
    """
    ensure_nonemptystring('name')

    val = _getlocal(inspect.currentframe(), name)
    if not isinstance(val, typ):
        raise ValueError('%s must be of type %s.' % (name, _describe(typ)))


def ensure_noneorinstance(
    name: str, typ: Union[type, Tuple[type, ...]]
) -> None:
    """Ensure name is either None or of classe typ.

    # Required parameters

    - name: a string, the name of the local variable to check
    - typ: a type or a tuple of types

    # Raised exceptions

    Raise _ValueError_ if the condition is not satisfied.
    """
    ensure_nonemptystring('name')

    val = _getlocal(inspect.currentframe(), name)
    if not _isnoneorinstance(val, typ):
        raise ValueError(
            '%s must be either None or of type %s.' % (name, _describe(typ))
        )


def ensure_nonemptystring(name: str) -> None:
    """Ensure name is a non-empty string.

    # Required parameters

    - name: a string, the name of the local variable to check

    # Raised exceptions

    Raise _ValueError_ if the condition is not satisfied.
    """
    # we have to check parameter validity, but a recursive call won't do
    if not _isnonemptystring(name):
        raise ValueError('Parameter \'name\' must be a string.')

    val = _getlocal(inspect.currentframe(), name)
    if not _isnonemptystring(val):
        raise ValueError('%s must be a non-empty string.' % name)


def ensure_noneornonemptystring(name: str) -> None:
    """Ensure name is either None or a non-empty string.

    # Required parameters

    - name: a string, the name of the local variable to check

    # Raised exceptions

    Raise _ValueError_ if the condition is not satisfied.
    """
    ensure_nonemptystring('name')

    val = _getlocal(inspect.currentframe(), name)
    if not _isnoneornonemptystring(val):
        raise ValueError('%s must be a non-empty string if specified.' % name)


def ensure_onlyone(name1: str, name2: str) -> None:
    """Ensure name1 or name2 is defined, but not both.

    # Required parameters

    - name1: a string, the name of a local variable to check
    - name2: a string, the name of a local variable to check

    # Raised exceptions

    Raise _ValueError_ if the condition is not satisfied.
    """
    ensure_nonemptystring('name1')
    ensure_nonemptystring('name2')

    val1 = _getlocal(inspect.currentframe(), name1)
    val2 = _getlocal(inspect.currentframe(), name2)
    if val1 is None and val2 is None:
        raise ValueError('Either %s or %s must be specified.' % (name1, name2))
    if val1 is not None and val2 is not None:
        raise ValueError(
            '%s and %s cannot be specified simultaneously.' % (name1, name2)
        )


def ensure_in(name: str, values: Iterable[str]) -> None:
    """Ensure name value is in values.

    # Required parameters

    - name: a string, the name of a local variable to check
    - values: a list of strings

    # Raised exceptions

    Raise _ValueError_ if the condition is not satisfied.
    """
    ensure_nonemptystring('name')

    val = _getlocal(inspect.currentframe(), name)

    if val not in values:
        raise ValueError(
            '%s not an allowed value, expecting one of %s.'
            % (val, ', '.join(values))
        )
