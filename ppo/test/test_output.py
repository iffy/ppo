from unittest import TestCase

from StringIO import StringIO


from ppo.output import giganticGrep


class giganticGrepTest(TestCase):

    def assertValue(self, indata, expected_output, message=None):
        """
        Assert that the given input results in the expected_output.
        """
        outstream = StringIO()
        giganticGrep(indata, outstream)
        value = outstream.getvalue()
        self.assertEqual(value, expected_output, message)

    def assertLines(self, indata, expected_output, message=None):
        """
        Assert that the given input results in the expected_output lines.
        """
        outstream = StringIO()
        giganticGrep(indata, outstream)
        value = outstream.getvalue()
        actual_lines = value.split('\n')
        expected_lines = expected_output + ['']

        present = set(expected_lines) & set(actual_lines)
        missing = set(expected_lines) - set(actual_lines)
        extra = set(actual_lines) - set(expected_lines)

        if missing or extra:
            self.fail('Expected these lines:\n%s\n\nPresent:\n%s\n\nExtra:\n%s\n\nMissing:\n%s' % (
                '\n'.join(expected_output),
                '\n'.join(list(present)),
                '\n'.join(list(extra)),
                '\n'.join(list(missing))))

    def test_dict(self):
        """
        A dict should be flattened into a single line with all fields.
        """
        self.assertValue(
            {'foo': 'foo', 'bar': 43, 'zippy': 'zoo'},
            'bar:\t43\tfoo:\tfoo\tzippy:\tzoo\n'
        )

    def test_nested_dict(self):
        """
        A dict within a dict should be flattened too
        """
        self.assertLines(
            {
                'foo': 'foo',
                'bar': {
                    'a': 'apple',
                    'b': 'banana',
                },
                'zoo': 'hoo',
            },
            [
                'bar:\ta:\tapple\tb:\tbanana\tfoo:\tfoo\tzoo:\thoo',
            ])

    def test_multi_nested_dict(self):
        """
        A dict with multiple nested dicts should flatten them one at a time.
        """
        self.assertLines(
            {
                'foo': 'foo',
                'bar': {
                    'a': 'apple',
                    'b': 'banana',
                },
                'car': {
                    'a': 'apple',
                    'b': 'banana',
                },
                'dog': [
                    1,2,'foo',
                ]
            },
            [
                'bar:\ta:\tapple\tb:\tbanana\tcar:\ta:\tapple\tb:\tbanana\tfoo:\tfoo',
                'bar:\ta:\tapple\tb:\tbanana\tcar:\ta:\tapple\tb:\tbanana\tfoo:\tfoo\tdog:\t1',
                'bar:\ta:\tapple\tb:\tbanana\tcar:\ta:\tapple\tb:\tbanana\tfoo:\tfoo\tdog:\t2',
                'bar:\ta:\tapple\tb:\tbanana\tcar:\ta:\tapple\tb:\tbanana\tfoo:\tfoo\tdog:\tfoo',
            ]
        )

    def test_list(self):
        """
        A list will have each thing printed on a line.
        """
        self.assertValue(
            ['foo', 'bar', 'hello'],
            'foo\nbar\nhello\n')

    def test_dict_with_list(self):
        """
        A dict with lists should permute the lists
        """
        self.assertLines({
                'host': '10.0.0.1',
                'roo': [
                    'A',
                    'B',
                    'C',
                ],
                'zoo': [
                    1,
                    2,
                ]
            },
            [
                "host:\t10.0.0.1",
                "host:\t10.0.0.1\troo:\tA\tzoo:\t1",
                "host:\t10.0.0.1\troo:\tA\tzoo:\t2",
                "host:\t10.0.0.1\troo:\tB\tzoo:\t1",
                "host:\t10.0.0.1\troo:\tB\tzoo:\t2",
                "host:\t10.0.0.1\troo:\tC\tzoo:\t1",
                "host:\t10.0.0.1\troo:\tC\tzoo:\t2",
            ])

    def test_newlines(self):
        """
        Newlines should be treated as lists
        """
        self.assertLines({
            "foo": "something\nwith\nnewlines",
        }, [
            "foo:\tsomething",
            "foo:\twith",
            "foo:\tnewlines",
        ])

    def test_spaces(self):
        """
        Spaces should be preserved
        """
        self.assertLines({
            'foo bar': 'something here',
        },
            ["foo bar:\tsomething here"])


    def test_unicode(self):
        """
        Unicode should be okay.
        """
        self.assertValue({
            'snowman': u'\N{SNOWMAN}',
            'something': 'not a snowman',
        },
            u"snowman:\t\N{SNOWMAN}\tsomething:\tnot a snowman\n".encode('utf-8'))

    def test_empty_list(self):
        """
        Empty lists should be marked as empty.
        """
        self.assertLines({
            'hosts': [],
            'foo': 'something',
            'another': [1,2],
        }, [
            'foo:\tsomething\thosts:\t',
            'foo:\tsomething\thosts:\t\tanother:\t1',
            'foo:\tsomething\thosts:\t\tanother:\t2',
        ])
