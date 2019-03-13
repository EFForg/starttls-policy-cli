""" Tests for main.py """
import unittest
import sys
import mock

from starttls_policy_cli import main

class TestArguments(unittest.TestCase):
    """Testing argument parser"""

    def test_no_args_require_generate(self):
        # pylint: disable=protected-access
        sys.argv = ["_"]
        parser = main._argument_parser()
        parser.error = mock.MagicMock(side_effect=Exception)
        self.assertRaises(Exception, parser.parse_args)

    def test_generate_no_arg(self):
        # pylint: disable=protected-access
        sys.argv = ["_", "--generate"]
        parser = main._argument_parser()
        parser.error = mock.MagicMock(side_effect=Exception)
        self.assertRaises(Exception, parser.parse_args)

    def test_generate_arg(self):
        # pylint: disable=protected-access
        sys.argv = ["_", "--generate", "postfix"]
        parser = main._argument_parser()
        arguments = parser.parse_args()
        self.assertEqual(arguments.generate, "postfix")

    def test_default_dir(self):
        # pylint: disable=protected-access
        sys.argv = ["_", "--generate", "postfix"]
        parser = main._argument_parser()
        arguments = parser.parse_args()
        self.assertEqual(arguments.policy_dir, "/etc/starttls-policy/")

    def test_policy_dir(self):
        # pylint: disable=protected-access
        sys.argv = ["_", "--generate", "postfix", "--policy-dir", "lmao"]
        parser = main._argument_parser()
        arguments = parser.parse_args()
        self.assertEqual(arguments.policy_dir, "lmao")

class TestPerform(unittest.TestCase):
    """Testing perform() main function and some subroutines"""
    def test_generate_unknown(self):
        # pylint: disable=protected-access
        sys.argv = ["_", "--generate", "lmao"]
        parser = main._argument_parser()
        parser.error = mock.MagicMock(side_effect=Exception)
        self.assertRaises(Exception, parser.parse_args)

    @mock.patch("starttls_policy_cli.main._ensure_directory")
    def test_generate(self, ensure_directory):
        # pylint: disable=protected-access, unused-argument
        main.GENERATORS = {"exists": mock.MagicMock()}
        sys.argv = ["_", "--generate", "exists"]
        parser = main._argument_parser()
        main._generate(parser.parse_args())
        self.assertTrue(main.GENERATORS["exists"].called_with("/etc/starttls-policy"))

    @mock.patch("os.path.exists")
    @mock.patch("os.makedirs")
    def test_ensure_directory(self, mock_makedirs, mock_exists):
        # pylint: disable=protected-access
        mock_exists.return_value = True
        main._ensure_directory("")
        mock_makedirs.assert_not_called()
        mock_exists.return_value = False
        main._ensure_directory("")
        mock_makedirs.assert_called_once()

if __name__ == '__main__':
    unittest.main()
