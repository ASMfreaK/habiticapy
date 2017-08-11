import unittest
from unittest import mock
from unittest.mock import patch
import os
from contextlib import contextmanager
import tempfile
from textwrap import dedent
import responses
from habitipy import cli


class DevNull(object):
    def write(self, what):
        pass
    def flush(self):
        pass


@contextmanager
def to_devnull():
    import sys
    stdout = sys.stdout
    sys.stdout = DevNull()
    try:
        yield
    finally:
        sys.stdout = stdout


class TestCli(unittest.TestCase):
    def setUp(self):
        self.file = tempfile.NamedTemporaryFile(delete=False)
        with self.file:
            self.file.write(dedent("""
            [habitipy]
            url = https://habitica.com
            login = this-is-a-sample-login
            password = this-is-a-sample-password
            """).encode('utf-8'))

    def tearDown(self):
        os.remove(self.file.name)

    @patch.object(cli.TasksPrint, 'domain', 'testdomain')
    @patch.object(
        cli.TasksPrint, 'domain_format',
        mock.Mock(wraps=cli.TasksPrint.domain_format, return_value=''))
    @patch('habitipy.cli.prettify', mock.Mock(wraps=cli.prettify))
    @responses.activate
    def test_task_print(self):
        data = [{'first':1}, {'second':2}]
        more = [{'third':3}]
        responses.add(
            responses.GET,
            url='https://habitica.com/api/v3/tasks/user?type=testdomain',
            content_type='application/json',
            match_querystring=True,
            json=dict(data=data)
            )
        with patch.object(cli.TasksPrint, 'more_tasks', more),to_devnull():
            cli.TasksPrint.invoke(config_filename=self.file.name)
            self.assertTrue(cli.TasksPrint.domain_format.called)
            data.extend(more)
            data = [((x,),) for x in data]
            cli.TasksPrint.domain_format.assert_has_calls(data)
            self.assertTrue(cli.prettify.called)