from unittest import TestCase

from io import StringIO

import structlog
structlog.configure_once(logger_factory=structlog.twisted.LoggerFactory())


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
            'bar: 43 foo: foo zippy: zoo\n'
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
                'foo: foo zoo: hoo',
                'foo: foo zoo: hoo bar: a: apple b: banana',
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
                'foo: foo',
                'foo: foo bar: a: apple b: banana',
                'foo: foo car: a: apple b: banana',
                'foo: foo dog: 1',
                'foo: foo dog: 2',
                'foo: foo dog: foo',
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
                "host: 10.0.0.1",
                "host: 10.0.0.1 roo: A",
                "host: 10.0.0.1 roo: B",
                "host: 10.0.0.1 roo: C",
                "host: 10.0.0.1 zoo: 1",
                "host: 10.0.0.1 zoo: 2",
            ])

    def test_newlines(self):
        """
        Newlines should be stripped out.
        """
        self.assertValue({
            "foo": "something\nwith\nnewlines",
        },
        "foo: something_with_newlines\n")


    def test_spaces(self):
        """
        Spaces should be replaced with underscores
        """
        self.assertValue({
            'foo bar': 'something here',
        },
        "foo_bar: something_here\n")


    def test_unicode(self):
        """
        Unicode should be okay.
        """
        self.assertValue({
            'snowman': '\N{SNOWMAN}',
            'something': 'not a snowman',
        },
            "snowman: \N{SNOWMAN} something: not_a_snowman\n".encode('utf-8'))

    def test_empty_list(self):
        """
        Empty lists should be marked as empty.
        """
        self.assertLines({
            'hosts': [],
            'foo': 'something',
            'another': [1,2],
        }, [
            'foo: something hosts: []',
            'foo: something hosts: [] another: 1',
            'foo: something hosts: [] another: 2',
        ])
