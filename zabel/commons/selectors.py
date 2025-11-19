# Copyright (c) 2023 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

"""
This module provides a set of functions that handle _selectors_.

A selector is an expression that matches a JSON object (a dictionary).

For example,

    foo.bar in (abc, def)

will match

```json
{
  "foo": {
    "bar": "abc"
  },
  "baz": {
  }
}
```

The selector format is a superset of Kubernetes' field and label selectors.

Here are the possible selector formats:

```text
key                                # the key or label exists
!key                               # the key or label does not exist
key=value                          # the key exists and has the specified value
key==value                         # same (= and == are synonyms)
key!=value                         # the key exists but has a different value
                                   # or the key does not exist
key in (value1, value2, ...)       # the key exists and its value is in the list
key notin (value1, value2, ...)    # the key exists and has a value not in the
                                   # list or the key does not exist
(value1, value2, ...) in key       # the key contains at least one of the values
                                   # in the list (and possibly others)
(value1, value2, ...) notin key    # the key does not contain any of the values
                                   # in the list or the key does not exist
```

## Equality-based requirements

_Equality-_ or _inequality-based_ requirements allow filtering by field
or label keys and values.  Matching objects must satisfy all of the
specified field or label constraints, though they may have additional
fields or labels as well.

Three kinds of operators are admitted `=`, `==`, `!=`.  The first two
represent _equality_ (and are synonyms), while the latter represents
_inequality_.  For example:

```text
environment = production
tier != frontend
```

## Set-based requirements

_Set-based_ field and label requirements allow filtering keys according
to a set of values.  Three kinds of operators are supported: `in`,
`notin`, and `exists` (only the key identifier). For example:

```text
environment in (production, qa)
tier notin (frontend, backend)
partition
!partition
(tainted, running) in status
(sweet, sour) notin flavor
```

- The first example selects all resources with key equal to `environment`
  and value equal to `production` or `qa`.
- The second example selects all resources with key equal to `tier` and
  values other than `frontend` and `backend`, and all resources with no
  labels with the `tier` key.
- The third example selects all resources including a label with key
  `partition`; no values are checked.
- The fourth example selects all resources without a label with key
  `partition`; no values are checked.
- The fifth example selects all resources with key `status` and values
  containing `tainted` and/or `running` (and possibly others).
- The sixth example selects all resources with key `flavor` and values
  containing neither `sweet` nor `sour`, and all resources without
  a `flavor` field.

Similarly the comma separator acts as an _AND_ operator. So filtering
resources with a `partition` key (no matter the value) and with
`environment` different than `qa` can be achieved using
`partition,environment notin (qa)`.  The set-based field or label
selector is a general form of equality since `environment=production` is
equivalent to `environment in (production)`; similarly for `!=` and
`notin`.

Set-based requirements can be mixed with equality-based requirements.
For example:

    partition in (customerA, customerB),environment!=qa

## Field selectors

For field selectors, the key is a series of field names (letters, digits,
`-`, `_`, and `/` are allowed) separated by dots.

Here are examples of field selectors:

```text
apiVersion == v1
metadata.name == my-app-foo
(app) in spec.selector.matchLabels
```

They will match objects of the form:

```json hl_lines="2 4 12-14"
{
  "apiVersion": "v1",
  "metadata": {
    "name": "my-app-foo",
    "labels": {
      "app": "my-app",
      "app.domain/component": "backend"
    }
  },
  "spec": {
    "selector": {
      "matchLabels": {
        "app": "my-app"
      }
    }
  }
}
```

## Label selectors

For label selectors, the key is the label's name.  It may contain dots.

Here are examples of label selectors:

```text
app == my-app
app.domain/component in (frontend, backend)
```

They will match objects of the form:

```json hl_lines="4 5"
{
  "metadata": {
    "labels": {
      "app": "my-app",
      "app.domain/component": "backend"
    }
  }
}
```

!!! tip
    Label selectors are a specialized form of JSONPath selectors.  A
    label selector of `key op value` is strictly equivalent to the
    `$.metadata.labels['key'] op 'value'` JSONPath selector.

## JSONPath selectors

Field selector keys can also use a restricted form of JSONPath.  A
JSONPath key starts with a dollar sign (`$`) followed by a series of
field names (starting with a dot) or dictionary keys (quoted, between
brackets).  For example:

```text
$.metadata.name
$.metadata.labels.app
$.metadata.labels['app.domain']
$["foo.bar'"].spec.image
```

They will match objects of the form:

```json hl_lines="3 5-6 11"
{
  "metadata": {
    "name": "my-app-foo",
    "labels": {
      "app": "my-app",
      "app.domain": "backend"
    }
  },
  "foo.bar'": {
    "spec": {
      "image": "my-image:v1.2.3"
    }
  }
}
```

When a JSONPath key is used, the values, if any, must be quoted (that is,
surrounded by single or double quotes):

```text
$.metadata.name == 'my-app'
$.metadata.labels.app in ('my-app', "your-app")
$["foo.bar'"].spec.image != "my-image:latest"
```

JSONPath selectors can be mixed with field selectors.  For example:

    partition in (customerA, customerB),$.environment!="qa"

??? note "Restrictions from RFC 9535"
    [RFC 9535](https://datatracker.ietf.org/doc/html/rfc9535) defines
    JSONPath.  This implementation only supports a subset of the syntax:

    - Descendant segments and wildcard selectors are not allowed.
    - Bracketed segments can only be quoted strings.  Functions, filter
      selectors, and array indexes are not handled.

## JSONPointer selectors

Field selector keys can also use a restricted form of JSON pointers.  A
JSON pointer key starts with a slash (`/`) followed by a series of
field names or dictionary keys separated by slashes.  For example:

```text
/apiVersion
/metadata/name
/metadata/labels/app
/metadata/labels/app~1domain~1component
```

They will match objects of the form:

```json hl_lines="2 4 6-7"
{
  "apiVersion": "v1",
  "metadata": {
    "name": "my-app-foo",
    "labels": {
      "app": "my-app",
      "app/domain/component": "backend"
    }
  },
  "spec": {}
}
```

When a JSON pointer key is used, operators must be surrounded by spaces
and the values, if any, must be quoted (that is, surrounded by single or
double quotes):

```text
/metadata/name == 'my-app'
/metadata/labels/app in ('my-app', "your-app")
/foo.bar'/spec/image != "my-image:latest"
```

JSONPointer selectors can be mixed with other field selectors.  For
example:

    /partition in ('customerA', 'customerB'),$.environment!="qa"

??? note "Restrictions from RFC 6901"
    [RFC 6901](https://datatracker.ietf.org/doc/html/rfc6901) defines
    JSON pointers.  This implementation only supports a subset of the
    syntax:

    - Spaces and commas are not allowed in JSON pointer keys.
    - Array indexes are not handled.

## Usage

```python
from zabel.commons import selectors

foo = {'abc': 'def', 'ghi': {'jkl': 'secret'}, 'mno': 'pqr'}
bar = {'abc': 'def', 'ghi': {'jkl': 'secret2'}}

# You can use an expression as a selector
selectors.match(foo, 'ghi.jkl==secret')                    # true
selectors.match(bar, 'ghi.jkl==secret')                    # false

# You can compile the selector if you intend to reuse it often
sel = selectors.compile('ghi.jkl==secret')
selectors.match(foo, sel)                                  # true
selectors.match(bar, sel)                                  # false

# A selector can contain more than one expression
selectors.match(bar, 'abc,ghi.jkl')                        # true
selectors.match(foo, 'abc,ghi.jkl')                        # true

# All expressions must match
sel2 = selectors.compile('abc,ghi.jkl in (secret, secret2),!mno')
selectors.match(foo, sel2)                                 # false
selectors.match(bar, sel2)                                 # true

# You can use spaces after a comma or around an operator if you
# like, but not in a key or value
sel2 = selectors.compile('abc, ghi.jkl == secret, ! mno')  # ok
sel2 = selectors.compile('ghi . jkl == secret')            # invalid
sel2 = selectors.compile('ghi.jkl == my secret')           # invalid

# You must use JSONPath or JSONPointer selectors if you need
# spaces in your values
sel2 = selectors.compile('$.ghi.jkl == "my secret"')       # ok
sel2 = selectors.compile('/ghi/jkl == "my secret"')        # ok, too
```
"""

__all__ = ['compile', 'match', 'prepare']

from typing import Any, Dict, List, Optional, Set, Tuple, Union

import re

########################################################################
## Constants

Object = Dict[str, Any]
OpCode = Tuple[
    int, Union[str, List[str], None], bool, Union[str, Set[str], None]
]

# Simple selectors
KEY = r'([a-zA-Z_][a-z0-9A-Z-_./]*)'
VALUE = r'[a-z0-9A-Z-_./@:#]+'
SET = rf'\(\s*({VALUE}(?:\s*,\s*{VALUE})*)\s*\)'

EQUAL_EXPR = re.compile(rf'^\s*{KEY}\s*([=!]?=)\s*({VALUE})\s*(?:,|$)')
INSET_EXPR = re.compile(rf'^\s*{KEY}\s+(in|notin)\s+{SET}\s*(?:,|$)')
SETIN_EXPR = re.compile(rf'^\s*{SET}\s+(in|notin)\s+{KEY}\s*(?:,|$)')

# JSONPath and JSONPointer selectors (rfc9535 & rfc6901)
QVALUE = r'''('[^']*'|"[^"]*")'''
QSET = rf'\(\s*({QVALUE}(\s*,\s*{QVALUE})*)\s*\)'
DSEGMENT = r'\.([a-zA-Z_][a-z0-9A-Z_]*)'
BSEGMENT = rf'\[\s*{QVALUE}\s*\]'
PATH = rf'\$\s*({DSEGMENT}|{BSEGMENT})*'
POINTER = r'(/[^/, ]+)+'
SEGMENTS = rf'({PATH}|{POINTER})'

EQUAL_JEXPR = re.compile(rf'^\s*{SEGMENTS}\s*([=!]?=)\s*{QVALUE}\s*(?:,|$)')
INSET_JEXPR = re.compile(rf'^\s*{SEGMENTS}\s+(in|notin)\s+{QSET}\s*(?:,|$)')
SETIN_JEXPR = re.compile(rf'^\s*{QSET}\s+(in|notin)\s+{SEGMENTS}\s*(?:,|$)')

# Mixed
EXISTS_EXPR = re.compile(rf'^\s*({KEY}|{SEGMENTS})\s*(?:,|$)')
NEXISTS_EXPR = re.compile(rf'^\s*!\s*({KEY}|{SEGMENTS})\s*(?:,|$)')


########################################################################
## Selectors helpers

OP_RESOLV = 0x01
OP_EQUAL = 0x10
OP_EXIST = 0x20
OP_NEXIST = 0x40
OP_INSET = 0x80
OP_SETIN = 0x100


def _segs(segs: str) -> List[str]:
    if segs[0] == '/':
        return [
            p.replace('~1', '/').replace('~0', '~')
            for p in segs.lstrip('/').split('/')
        ]

    segs = segs[1:].lstrip()
    split: List[str] = []
    while segs:
        if match := re.match(DSEGMENT, segs):
            split.append(match.group(1))
            segs = segs[match.end() :]
        elif match := re.match(BSEGMENT, segs):
            split.append(match.group(1)[1:-1])
            segs = segs[match.end() :]
    return split


def _qvals(qvals: str) -> Set[str]:
    return {v[1:-1] for v in re.findall(QVALUE, qvals)}


def _vals(vals: str) -> Set[str]:
    return {v.strip() for v in vals.split(',')}


def compile(exprs: str, resolve_path: bool = True) -> List[OpCode]:
    """Compile selector.

    # Required parameters

    - exprs: a string, a comma-separated list of expressions

    # Optional parameters

    - resolve_path: a boolean, default True

    # Returned value

    A list of tuples, the 'compiled' selectors.

    # Raised exceptions

    A _ValueError_ exception is raised if at least one expression is
    invalid.

    # Usage

    `resolve_path` specifies whether a key containing dots should be
    interpreted or used literally.

    It is typically set to false when compiling label selectors.

    ```python
    field = selectors.compile('a.b.c', resolve_path=True)  # default
    selectors.match({'a': {'b': {'c': 34}}}, field)        # true

    label = selectors.compile('a.b.c', resolve_path=False)
    selectors.match({'a.b.c': 12}, label)                  # true
    ```
    """

    def _op(
        code: int,
        key: Union[str, List[str]],
        neq: bool = False,
        val: Union[str, Set[str], None] = None,
    ) -> OpCode:
        if not resolve_path and isinstance(key, list):
            raise ValueError(
                'JSONPath and JSONPointer not allowed in label selectors.'
            )
        if resolve_path and isinstance(key, str) and '.' in key:
            return code | OP_RESOLV, key.split('.'), neq, val
        if resolve_path and isinstance(key, list):
            return code | OP_RESOLV, key, neq, val
        return code, key, neq, val

    if not isinstance(exprs, str):
        raise ValueError(f'Invalid selector {exprs}, was expecting a string.')

    instrs = []
    while exprs.strip():
        # Simple and Mixed selectors
        if match := EQUAL_EXPR.match(exprs):
            key, ope, value = match.groups()
            instr = _op(OP_EQUAL, key, ope == '!=', value)
        elif match := EXISTS_EXPR.match(exprs):  # Mixed
            instr = _op(OP_EXIST, match.group(2) or _segs(match.group(3)))
        elif match := NEXISTS_EXPR.match(exprs):  # Mixed
            instr = _op(OP_NEXIST, match.group(2) or _segs(match.group(3)))
        elif match := INSET_EXPR.match(exprs):
            key, ope, vals = match.groups()
            instr = _op(OP_INSET, key, ope == 'notin', _vals(vals))
        elif match := SETIN_EXPR.match(exprs):
            vals, ope, key = match.groups()
            instr = _op(OP_SETIN, key, ope == 'notin', _vals(vals))

        # JSONPath & JSONPointer
        elif match := EQUAL_JEXPR.match(exprs):
            seg, _, _, _, _, ope, qvalue = match.groups()
            instr = _op(OP_EQUAL, _segs(seg), ope == '!=', qvalue[1:-1])
        elif match := INSET_JEXPR.match(exprs):
            seg, _, _, _, _, ope, qvals, _, _, _ = match.groups()
            instr = _op(OP_INSET, _segs(seg), ope == 'notin', _qvals(qvals))
        elif match := SETIN_JEXPR.match(exprs):
            qvals, _, _, _, ope, seg, _, _, _, _ = match.groups()
            instr = _op(OP_SETIN, _segs(seg), ope == 'notin', _qvals(qvals))

        # Invalid
        else:
            raise ValueError(f'Invalid selector expression {exprs}.')

        instrs.append(instr)
        exprs = exprs[match.end() :]

    return instrs


def _resolve_path(items: List[str], obj: Object) -> Tuple[bool, Optional[Any]]:
    current = obj
    for key in items:
        if not isinstance(current, dict) or key not in current:
            return False, None
        current = current[key]
    return True, current


def _evaluate(obj: Object, req: OpCode) -> bool:
    """Evaluate whether obj matches selector."""
    opcode, key, neq, arg = req
    if opcode == OP_EQUAL:  # fast path
        if key in obj:
            return (str(obj[key]) == arg) ^ neq
        return neq

    if opcode & OP_RESOLV:
        found, value = _resolve_path(key, obj)  # type: ignore
    else:
        found, value = key in obj, obj.get(key)  # type: ignore

    if opcode & OP_EXIST:
        return found

    if opcode & OP_NEXIST:
        return not found

    if found and opcode & OP_SETIN:
        return any(v in (value or {}) for v in arg) ^ neq  # type: ignore
    if found and opcode & OP_EQUAL:
        return (str(value) == arg) ^ neq
    if found:  # OP_INSET
        return (str(value) in arg) ^ neq  # type: ignore
    return neq


def match_compiledfieldselector(obj: Object, opcodes: List[OpCode]) -> bool:
    return all(_evaluate(obj, opcode) for opcode in opcodes)


def match_compiledlabelselector(obj: Object, opcodes: List[OpCode]) -> bool:
    labels = obj.get('metadata', {}).get('labels', {})
    return all(_evaluate(labels, opcode) for opcode in opcodes)


def match(
    obj: Object,
    fieldselector: Union[None, str, List[OpCode]] = None,
    labelselector: Union[None, str, List[OpCode]] = None,
) -> bool:
    """Check if object matches selector.

    # Required parameters

    - obj: a dictionary

    # Optional parameters

    - fieldselector: a string or a list of opcodes or None
    - labelselector: a string or a list of opcodes or None

    # Returned value

    A boolean.

    # Raised exceptions

    A _ValueError_ exception is raised if `fieldselector` or
    `labelselector` is not a valid.

    # Usage

    An empty selector matches.  The selectors can be strings or
    compiled selectors.

    A string selector is of form:

        [expr[,expr]*[,]]

    where `expr` is one of `key`, `!key`, or `key op value`, with `op`
    being one of `=`, `==`, or `!=`.  The `key in (value[, value...])`,
    `key notin (value[, value...])`, `(value[, value...]) in key`, and
    `(value[, value...]) notin key` set-based requirements are also
    implemented.

    Field selectors are applied to the object itself, while label
    selectors are applied to the `metadata.labels` dictionary of the
    object (or an empty dictionary if the object has no `metadata` or
    no `labels`).
    """
    if isinstance(fieldselector, str):
        fieldselector = compile(fieldselector)
    if isinstance(labelselector, str):
        labelselector = compile(labelselector, resolve_path=False)
    return (
        not fieldselector or match_compiledfieldselector(obj, fieldselector)
    ) and (
        not labelselector or match_compiledlabelselector(obj, labelselector)
    )


def prepare(
    src: Any,
) -> Tuple[Optional[List[OpCode]], Optional[List[OpCode]]]:
    """Prepare selectors if defined.

    `src` is typically a request arg dictionary.  It must implement the
    `get()` protocol.  The selectors, `fieldSelector` and
    `labelSelector`, are compiled if found in `src`.

    # Required parameters

    - src: a dictionary-like structure

    # Returned value

    A `(fieldselector, labelselector)` pair of lists of opcodes or None.

    # Raised exceptions

    A _ValueError_ exception is raised if the selectors defined in `src`
    are not a valid.
    ."""
    fieldselector = src.get('fieldSelector')
    labelselector = src.get('labelSelector')

    if fieldselector:
        fieldselector = compile(fieldselector)
    if labelselector:
        labelselector = compile(labelselector, resolve_path=False)
    return fieldselector, labelselector
