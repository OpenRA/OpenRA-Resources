from unittest import TestCase
from unittest.mock import patch
from openra.classes.exceptions import ExceptionBase

from openra.facades import log
from freezegun import freeze_time

class TestServiceLog(TestCase):

    @patch('builtins.print')
    @freeze_time('1996-11-22 11:22:33')
    def test_will_print_info(self, print_mock):
        log().info('test')

        print_mock.assert_called_once_with('1996-11-22 11:22:33 info: test')

    @patch('builtins.print')
    @freeze_time('1996-11-22 11:22:33')
    def test_will_print_warnings(self, print_mock):
        log().warning('test2')

        print_mock.assert_called_once_with('1996-11-22 11:22:33 warning: test2')

    @patch('builtins.print')
    @freeze_time('1996-11-22 11:22:33')
    def test_will_print_errors(self, print_mock):
        log().error('test3')

        print_mock.assert_called_once_with('1996-11-22 11:22:33 error: test3')

    @patch('builtins.print')
    @freeze_time('1996-11-22 11:22:33')
    def test_will_print_exception_objs(self, print_mock):
        exception = ExceptionBase()

        log().exception_obj(exception)

        print_mock.assert_called_once_with('1996-11-22 11:22:33 exception: '+exception.get_full_details())
