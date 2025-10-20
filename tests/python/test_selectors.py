# Copyright (c) 2023 Henix, Henix.fr
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Expressions unit tests."""

import unittest

from zabel.commons import selectors


########################################################################

RESOLVPATH_DATA = {'foo': {'bar': {'baz': 'bAZ'}}}
NOPATH_DATA = {'foo': 'bar', 'baz': 'bAZ'}
LABELS_DATA = {'foo.bar.baz': 'bAZ', 'foo': 'fOO'}
METADATALABELS_DATA = {'metadata': {'labels': LABELS_DATA}}
FIELDS_DATA = {'generator': 'opentestfactory.org/template.generator@v1'}


########################################################################


class TestSelectors(unittest.TestCase):
    def test_resolve_path_1(self):
        status, value = selectors._resolve_path(
            'foo.bar.baz'.split('.'), RESOLVPATH_DATA
        )
        self.assertTrue(status)
        self.assertEqual(value, 'bAZ')

    def test_resolve_path_2(self):
        status, value = selectors._resolve_path(
            'foo.bar.foobar'.split('.'), RESOLVPATH_DATA
        )
        self.assertFalse(status)
        self.assertIsNone(value)

    def test_evaluate_fields_1(self):
        self.assertTrue(selectors.match(RESOLVPATH_DATA, fieldselector=''))

    def test_evaluate_fields_2(self):
        self.assertTrue(
            selectors.match(RESOLVPATH_DATA, fieldselector='foo.bar.baz==bAZ')
        )

    def test_evaluate_fields_3(self):
        self.assertFalse(
            selectors.match(RESOLVPATH_DATA, fieldselector='foo.bar.baz!=bAZ')
        )

    def test_evaluate_fields_4(self):
        self.assertTrue(
            selectors.match(RESOLVPATH_DATA, fieldselector='foo.bar.baz')
        )

    def test_evaluate_fields_5(self):
        self.assertFalse(
            selectors.match(RESOLVPATH_DATA, fieldselector='!foo.bar.baz')
        )

    def test_evaluate_fields_6(self):
        self.assertFalse(
            selectors.match(RESOLVPATH_DATA, fieldselector='foo.bar.foobar')
        )

    def test_evaluate_fields_7(self):
        self.assertTrue(
            selectors.match(RESOLVPATH_DATA, fieldselector='!foo.bar.foobar')
        )

    def test_evaluate_fields_8(self):
        self.assertTrue(
            selectors.match(
                RESOLVPATH_DATA, fieldselector='foo.bar.baz in (bar, bAZ)'
            )
        )

    def test_evaluate_fields_9(self):
        self.assertFalse(
            selectors.match(
                RESOLVPATH_DATA, fieldselector='foo.bar.baz in (bar, baz)'
            )
        )

    def test_evaluate_fields_10(self):
        self.assertTrue(
            selectors.match(
                RESOLVPATH_DATA, fieldselector='foo.bar.baz notin (bar, baz)'
            )
        )

    def test_evaluate_fields_11(self):
        self.assertFalse(
            selectors.match(
                RESOLVPATH_DATA, fieldselector='foo.bar.foobar in (bar, bAZ)'
            )
        )

    def test_evaluate_fields_12(self):
        self.assertTrue(
            selectors.match(
                RESOLVPATH_DATA,
                fieldselector='foo.bar.foobar notin (bar, baz)',
            )
        )

    def test_evaluate_fields_13(self):
        self.assertRaises(
            ValueError,
            selectors.match,
            RESOLVPATH_DATA,
            fieldselector='foo.bar.baz * 2',
        )

    # _evaluate

    def test_evaluate_opequal_ok(self):
        self.assertTrue(
            selectors._evaluate(
                LABELS_DATA,
                (selectors.OP_EQUAL, 'foo.bar.baz', False, 'bAZ'),
            )
        )

    def test_evaluate_opequal_nok(self):
        self.assertFalse(
            selectors._evaluate(
                LABELS_DATA, (selectors.OP_EQUAL, 'foo.bar.baz', True, 'bAZ')
            )
        )

    def test_evaluate_opexist_ok(self):
        self.assertTrue(
            selectors._evaluate(
                LABELS_DATA,
                (selectors.OP_EXIST, 'foo.bar.baz', None, None),
            )
        )

    def test_evaluate_opnexist_nok(self):
        self.assertFalse(
            selectors._evaluate(
                LABELS_DATA,
                (selectors.OP_NEXIST, 'foo.bar.baz', None, None),
            )
        )

    def test_evaluate_opexist_nok(self):
        self.assertFalse(
            selectors._evaluate(
                LABELS_DATA,
                (selectors.OP_EXIST, 'foo.bar.foobar', None, None),
            )
        )

    def test_evaluate_opnexist_ok(self):
        self.assertTrue(
            selectors._evaluate(
                LABELS_DATA,
                (selectors.OP_NEXIST, 'foo.bar.foobar', None, None),
            )
        )

    def test_evaluate_opset_in_ok(self):
        self.assertTrue(
            selectors._evaluate(
                LABELS_DATA,
                (selectors.OP_INSET, 'foo.bar.baz', False, {'bar', 'bAZ'}),
            )
        )

    def test_evaluate_opset_in_nok(self):
        self.assertFalse(
            selectors._evaluate(
                LABELS_DATA,
                (selectors.OP_INSET, 'foo.bar.baz', False, {'bar', 'baz'}),
            )
        )

    def test_evaluate_opset_notin_ok(self):
        self.assertTrue(
            selectors._evaluate(
                LABELS_DATA,
                (selectors.OP_INSET, 'foo.bar.baz', True, {'bar', 'baz'}),
            )
        )

    def test_evaluate_opset_in_badkey(self):
        self.assertFalse(
            selectors._evaluate(
                LABELS_DATA,
                (selectors.OP_INSET, 'foo.bar.foobar', False, {'bar', 'bAZ'}),
            )
        )

    def test_evaluate_opset_notin_badkey_ok(self):
        self.assertTrue(
            selectors._evaluate(
                LABELS_DATA,
                (selectors.OP_INSET, 'foo.bar.foobar', True, {'bar', 'bAZ'}),
            )
        )

    def test_evaluate_13(self):
        self.assertTrue(
            selectors._evaluate(
                FIELDS_DATA,
                (
                    selectors.OP_EQUAL,
                    'generator',
                    False,
                    'opentestfactory.org/template.generator@v1',
                ),
            )
        )

    def test_matchfieldselector_1(self):
        self.assertTrue(selectors.match(RESOLVPATH_DATA, fieldselector=''))

    def test_matchfieldselector_2(self):
        self.assertTrue(selectors.match(RESOLVPATH_DATA, fieldselector='foo'))

    def test_matchfieldselector_2_(self):
        self.assertTrue(
            selectors.match(RESOLVPATH_DATA, fieldselector='foo.bar')
        )

    def test_matchfieldselector_3(self):
        self.assertTrue(
            selectors.match(RESOLVPATH_DATA, fieldselector='foo,foo.bar')
        )

    def test_matchfieldselector_4(self):
        self.assertFalse(
            selectors.match(RESOLVPATH_DATA, fieldselector='foo,foobar')
        )

    def test_matchfieldselector_5(self):
        self.assertTrue(
            selectors.match(RESOLVPATH_DATA, fieldselector='foo.bar.baz')
        )

    def test_matchfieldselector_6(self):
        self.assertTrue(
            selectors.match(RESOLVPATH_DATA, fieldselector='foo,!bar')
        )

    def test_matchfieldselector_7(self):
        self.assertTrue(
            selectors.match(
                RESOLVPATH_DATA, fieldselector='foo,foo.bar.baz==bAZ'
            )
        )

    def test_matchfieldselector_path_notfound_equal(self):
        self.assertFalse(
            selectors.match(NOPATH_DATA, fieldselector='foo.foobar==bAZ')
        )

    def test_matchfieldselector_path_notfound_notequal(self):
        self.assertTrue(
            selectors.match(NOPATH_DATA, fieldselector='foo.foobar!=bAZ')
        )

    def test_matchfieldselector_nopath_notfound_equal(self):
        self.assertFalse(
            selectors.match(NOPATH_DATA, fieldselector='foobar==bAZ')
        )

    def test_matchfieldselector_nopath_notfound_notequal(self):
        self.assertTrue(
            selectors.match(NOPATH_DATA, fieldselector='foobar!=bAZ')
        )

    def test_matchlabelselector_1(self):
        self.assertTrue(selectors.match(METADATALABELS_DATA, labelselector=''))

    def test_matchlabelselector_2(self):
        self.assertTrue(
            selectors.match(METADATALABELS_DATA, labelselector='foo')
        )

    def test_matchlabelselector_2_(self):
        self.assertFalse(
            selectors.match(METADATALABELS_DATA, labelselector='foo.bar')
        )

    def test_matchlabelselector_3(self):
        self.assertTrue(
            selectors.match(
                METADATALABELS_DATA, labelselector='foo,foo.bar.baz'
            )
        )

    def test_matchlabelselector_4(self):
        self.assertFalse(
            selectors.match(METADATALABELS_DATA, labelselector='foo,foobar')
        )

    def test_matchlabelselector_5(self):
        self.assertTrue(
            selectors.match(
                METADATALABELS_DATA, labelselector='foo in (foo, fOO),!bar'
            )
        )

    def test_matchlabelselector_6(self):
        self.assertTrue(
            selectors.match(METADATALABELS_DATA, labelselector='foo,!bar')
        )

    def test_matchlabelselector_7(self):
        self.assertTrue(
            selectors.match(
                METADATALABELS_DATA, labelselector='foo,foo.bar.baz==bAZ'
            )
        )

    # compile

    def test_compile_notastring(self):
        self.assertRaises(ValueError, selectors.compile, 123)

    def test_compile(self):
        self.assertRaisesRegex(
            ValueError,
            'Invalid selector expression foo>12',
            selectors.compile,
            'foo>12',
        )

    def test_compile_badvalue(self):
        self.assertRaisesRegex(
            ValueError,
            'Invalid selector expression foo==not_?.',
            selectors.compile,
            'foo==not_ok?',
        )

    def test_compile_urlvalue(self):
        _ = selectors.compile('foo==http://example.com')

    # match

    def test_match_noselectorsisyes(self):
        self.assertTrue(selectors.match({}))

    def test_match_badfieldselector_fails(self):
        self.assertRaises(
            ValueError, selectors.match, {}, fieldselector='x > 2'
        )

    def test_match_badlabelselector_fails(self):
        self.assertRaises(
            ValueError, selectors.match, {}, labelselector='x > 2'
        )

    def test_match_both_str_ok(self):
        self.assertTrue(
            selectors.match(
                {'foo': 'bar', 'metadata': {'labels': {'bar': 'baz'}}},
                fieldselector='foo==bar',
                labelselector='bar==baz',
            )
        )

    def test_match_bad_labelselector_brackets(self):
        self.assertRaises(
            ValueError,
            selectors.match,
            {'foo': 'bar', 'metadata': {'labels': {'bar': 'baz'}}},
            labelselector='$.bar["foo"]=="baz"',
        )

    def test_match_fieldselector_doublebrackets_ok(self):
        self.assertTrue(
            selectors.match(
                {'foo': 'bar', 'metadata': {'labels': {'bar': 'baz'}}},
                fieldselector='$.metadata["labels"][\'bar\']==\'baz\'',
            )
        )

    def test_match_fieldselector_doublebrackets_bad(self):
        self.assertFalse(
            selectors.match(
                {'foo': 'bar', 'metadata': {'labels': {'bar': 'baz'}}},
                fieldselector='$ .foo[   "b"]',
            )
        )

    def test_match_fieldselector_bracketsequal(self):
        self.assertTrue(
            selectors.match(
                {
                    'foo': 'bar',
                    'metadata': {'annotations': {'foo.bar': 'baz'}},
                },
                fieldselector='$.metadata.annotations["foo.bar"]=="baz"   ',
            )
        )

    def test_match_fieldselector_bracketin(self):
        self.assertTrue(
            selectors.match(
                {
                    'foo': 'bar',
                    'metadata': {'annotations': {'foo.bar': 'baz'}},
                },
                fieldselector='$.metadata.annotations["foo.bar"  ] in ("foobar"  , "baz" )',
            )
        )

    def test_match_fieldselector_inbracket(self):
        self.assertTrue(
            selectors.match(
                {
                    'foo': 'bar',
                    'metadata': {'annotations': {'foo.bar': ['baz']}},
                },
                fieldselector='("baz") in $.metadata.annotations["foo.bar"]',
            )
        )

    def test_match_fieldselector_bracketexists(self):
        self.assertTrue(
            selectors.match(
                {
                    'foo': 'bar',
                    'metadata': {'annotations': {'foo.bar': 'baz'}},
                },
                fieldselector='$.metadata.annotations["foo.bar"]',
            )
        )

    def test_match_fieldselector_bracketnotexists(self):
        self.assertFalse(
            selectors.match(
                {
                    'foo': 'bar',
                    'metadata': {'annotations': {'foo.bar': 'baz'}},
                },
                fieldselector='!$.metadata.annotations["foo.bar"]',
            )
        )

    def test_match_setin_none_invalid(self):
        self.assertFalse(
            selectors.match({'foo': None}, fieldselector='(a) in foo')
        )

    def test_match_setin_notfound_invalid(self):
        self.assertFalse(
            selectors.match({'foo': 'bar'}, fieldselector='(a) in foo.bar')
        )

    def test_match_setin_notfound_one_ok(self):
        self.assertFalse(
            selectors.match({'foo': 'bar'}, fieldselector='(a) in baz')
        )

    def test_match_setin_notfound_one_nok(self):
        self.assertTrue(
            selectors.match({'foo': 'bar'}, fieldselector='(z) notin baz')
        )

    def test_match_setin_string_one_ok(self):
        self.assertTrue(
            selectors.match(
                {'foo': 'bar', 'spec': {'string': 'abcdef'}},
                fieldselector='(abc) in spec.string',
            )
        )

    def test_match_setin_string_one_nok(self):
        self.assertFalse(
            selectors.match(
                {'foo': 'bar', 'spec': {'string': 'abcdef'}},
                fieldselector='(cba) in spec.string',
            )
        )

    def test_match_setnotin_string_one_ok(self):
        self.assertFalse(
            selectors.match(
                {'foo': 'bar', 'spec': {'string': 'abcdef'}},
                fieldselector='(abc) notin spec.string',
            )
        )

    def test_match_setnotin_string_one_nok(self):
        self.assertTrue(
            selectors.match(
                {'foo': 'bar', 'spec': {'string': 'abcdef'}},
                fieldselector='(cba) notin spec.string',
            )
        )

    def test_match_setin_array_one_ok(self):
        self.assertTrue(
            selectors.match(
                {'foo': 'bar', 'spec': {'array': ['a', 'b', 'c']}},
                fieldselector='(a) in spec.array',
            )
        )

    def test_match_setin_array_one_nok(self):
        self.assertFalse(
            selectors.match(
                {'foo': 'bar', 'spec': {'array': ['a', 'b', 'c']}},
                fieldselector='(z) in spec.array',
            )
        )

    def test_match_setin_array_two_ok(self):
        self.assertTrue(
            selectors.match(
                {'foo': 'bar', 'spec': {'array': ['a', 'b', 'c']}},
                fieldselector='(a, c) in spec.array',
            )
        )

    def test_match_setin_array_two_nok(self):
        self.assertTrue(
            selectors.match(
                {'foo': 'bar', 'spec': {'array': ['a', 'b', 'c']}},
                fieldselector='(z, c) in spec.array',
            )
        )

    def test_match_setnotin_array_two_ok(self):
        self.assertFalse(
            selectors.match(
                {'foo': 'bar', 'spec': {'array': ['a', 'b', 'c']}},
                fieldselector='(a, c) notin spec.array',
            )
        )

    def test_match_setnotin_array_two_nok(self):
        self.assertFalse(
            selectors.match(
                {'foo': 'bar', 'spec': {'array': ['a', 'b', 'c']}},
                fieldselector='(z, c) notin spec.array',
            )
        )

    def test_match_in_array_nok(self):
        self.assertFalse(
            selectors.match(
                {'foo': 'bar', 'spec': {'array': ['a', 'b', 'c']}},
                fieldselector='spec.array in (windows)',
            )
        )

    def test_match_notin_array_ok(self):
        self.assertTrue(
            selectors.match(
                {'foo': 'bar', 'spec': {'array': ['a', 'b', 'c']}},
                fieldselector='spec.array notin (windows)',
            )
        )

    def test_match_intin_ok(self):
        self.assertTrue(
            selectors.match(
                {'foo': 'bar', 'status': {'count': 0}},
                fieldselector='status.count in (0, 1)',
            )
        )

    def test_match_intequal_ok(self):
        self.assertTrue(
            selectors.match(
                {'foo': 'bar', 'status': {'count': 123}},
                fieldselector='status.count == 123',
            )
        )

    def test_match_intequal_nok(self):
        self.assertFalse(
            selectors.match(
                {'foo': 'bar', 'status': {'count': 100}},
                fieldselector='status.count == 123',
            )
        )

    def test_match_both_str_nomatch(self):
        self.assertFalse(
            selectors.match(
                {'foo': 'bar', 'metadata': {'labels': {'bar': 'baz'}}},
                fieldselector='foo==bar',
                labelselector='bar==bAZ',
            )
        )

    def test_match_both_compiled_ok(self):
        self.assertTrue(
            selectors.match(
                {'foo': 'bar', 'metadata': {'labels': {'bar.foo': 'baz'}}},
                fieldselector=selectors.compile('foo==bar'),
                labelselector=selectors.compile(
                    'bar.foo==baz', resolve_path=False
                ),
            )
        )

    def test_match_both_compiled_nomatch(self):
        self.assertFalse(
            selectors.match(
                {'foo': 'bar', 'metadata': {'labels': {'bar.foo': 'baz'}}},
                fieldselector=selectors.compile('foo==bar'),
                labelselector=selectors.compile(
                    'bar.foo==bAZ', resolve_path=False
                ),
            )
        )

    # root element

    def test_match_root_string_ok(self):
        self.assertTrue(
            selectors.match('hello world', fieldselector='("hello") in $')
        )

    def test_match_root_string_nok(self):
        self.assertFalse(
            selectors.match('hello world', fieldselector='("hello2") in $')
        )

    def test_match_root_array_ok(self):
        self.assertTrue(
            selectors.match(['hello', 'world'], fieldselector='("world") in $')
        )

    def test_match_root_array_nok(self):
        self.assertFalse(
            selectors.match(
                ['hello', 'world'], fieldselector='("hello2") in $'
            )
        )

    def test_match_pointer_nok(self):
        self.assertFalse(
            selectors.match(
                {'hello': 'world'}, fieldselector='/hello == "hello2"'
            )
        )

    def test_match_pointer_ok(self):
        self.assertTrue(
            selectors.match(
                {'hello': {'world': 12}}, fieldselector='/hello/world == "12"'
            )
        )

    def test_match_pointer_escape_ok(self):
        self.assertTrue(
            selectors.match(
                {'hello': {'world/2': 12}},
                fieldselector='/hello/world~12 == "12"',
            )
        )

    def test_match_pointer_escape2_ok(self):
        self.assertTrue(
            selectors.match(
                {'hello': {'world~12': 12}},
                fieldselector='/hello/world~012 == "12"',
            )
        )

    def test_match_pointer_multi_ok(self):
        self.assertTrue(
            selectors.match(
                {'hello': {'world~12': 12}},
                fieldselector='/hello,/hello/world~012',
            )
        )

    # prepare

    def test_prepare_none(self):
        f, l = selectors.prepare({})
        self.assertIsNone(f)
        self.assertIsNone(l)

    def test_prepare_fielddefined(self):
        f, l = selectors.prepare({'fieldSelector': 'foo'})
        self.assertIsNotNone(f)
        self.assertIsNone(l)

    def test_prepare_labeldefined(self):
        f, l = selectors.prepare({'labelSelector': 'foo.bar'})
        self.assertIsNone(f)
        self.assertIsNotNone(l)
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0][1], 'foo.bar')

    def test_prepare_bothdefined(self):
        f, l = selectors.prepare(
            {'fieldSelector': 'foo.bar', 'labelSelector': 'foo.bar'}
        )
        self.assertIsNotNone(f)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0][1], ['foo', 'bar'])
        self.assertIsNotNone(l)
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0][1], 'foo.bar')

    def test_prepare_invalid(self):
        self.assertRaises(
            ValueError, selectors.prepare, {'fieldSelector': 'foo.bar>2'}
        )


if __name__ == '__main__':
    unittest.main()
