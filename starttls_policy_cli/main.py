""" Main entrypoint for starttls-policy CLI tool """
import argparse
import os

from starttls_policy_cli import configure

GENERATORS = {
    "postfix": configure.PostfixGenerator,
}

def _argument_parser():
    parser = argparse.ArgumentParser(
        description="Generates MTA configuration file according to STARTTLS-Everywhere policy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-g", "--generate",
                        choices=GENERATORS,
                        help="The MTA you want to generate a configuration file for.",
                        dest="generate", required=True)
    # TODO: decide whether to use /etc/ for policy list home
    parser.add_argument("-d", "--policy-dir",
                        help="Policy file directory on this computer.",
                        default="/etc/starttls-policy/", dest="policy_dir")
    parser.add_argument("-e", "--early-adopter",
                        help="Early Adopter mode. Processes all \"testing\" domains in policy list "
                        "same way as domains in \"enforce\" mode, effectively requiring strong TLS "
                        "for domains in \"testing\" mode too. This mode is useful for participating"
                        " in tests of recently added domains with real communications and earlier "
                        "security hardening at the cost of increased probability of delivery "
                        "degradation. Use this mode with awareness about all implications.",
                        action="store_true",
                        dest="early_adopter")
    return parser


def _ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def _generate(arguments):
    _ensure_directory(arguments.policy_dir)
    config_generator = GENERATORS[arguments.generate](arguments.policy_dir,
                                                      arguments.early_adopter)
    config_generator.generate()
    config_generator.manual_instructions()

def main():
    """ Entrypoint for CLI tool. """
    parser = _argument_parser()
    _generate(parser.parse_args())

if __name__ == "__main__":
    main()  # pragma: no cover
