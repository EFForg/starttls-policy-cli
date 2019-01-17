"""
Config generator
"""
import sys
import abc
import os
import six

from starttls_policy_cli import constants
from starttls_policy_cli import policy
from starttls_policy_cli import util

class ConfigGenerator(object):
    # pylint: disable=useless-object-inheritance
    """
    Generic configuration generator.
    The two primary public functions:
        generate()
        print_instruct()
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, policy_dir):
        self._policy_dir = policy_dir
        self._policy_filename = os.path.join(self._policy_dir, constants.POLICY_FILENAME)
        self._config_filename = os.path.join(self._policy_dir, self.default_filename)
        self._policy_config = None

    def _load_config(self):
        if self._policy_config is None:
            self._policy_config = policy.Config(filename=self._policy_filename)
            self._policy_config.load()
        return self._policy_config

    def _write_config(self, result, filename):
        with open(filename, "w") as config_file:
            six.print_(result, file=config_file)

    def _expired_warning(self):
        """Warns user about policy list expiration.
        """
        six.print_("\nACTION REQUIRED: your policy list at {config_location} has expired! "
                   "Generating empty config.\n"
                   "Check to see whether your update mechanism "
                   "(cronjob, systemd timer) is working.\n"
                       .format(config_location=self._policy_filename),
                   file=sys.stderr)

    def generate(self):
        """Generates and dumps MTA configuration file to `policy_dir`.
        """
        policy_list = self._load_config()
        expired = util.is_expired(policy_list.expires)
        if expired:
            self._expired_warning()
            self._generate_expired_fallback()
        else:
            self._generate(policy_list)

    def manual_instructions(self):
        """Prints manual installation instructions to stdout.
        """
        six.print_("{line}Manual installation instructions for {mta_name}{line}{instructions}"
            .format(line="\n" + ("-" * 50) + "\n",
                    mta_name=self.mta_name,
                    instructions=self._instruct_string()))

    @abc.abstractmethod
    def _generate(self, policy_list):
        """Creates configuration file(s) needed."""

    @abc.abstractmethod
    def _generate_expired_fallback(self):
        """Creates configuration file(s) for expired policy list.
        Returns a unicode string (text to write to file)."""

    @abc.abstractmethod
    def _instruct_string(self):
        """Explain how to install the configuration file that was generated."""

    @abc.abstractproperty
    def mta_name(self):
        """The name of the MTA this generator is for."""

    @abc.abstractproperty
    def default_filename(self):
        """The expected default filename of the generated configuration file."""

class PostfixGenerator(ConfigGenerator):
    """Configuration generator for postfix.
    """

    @staticmethod
    def _policy_for_domain(domain, tls_policy, max_domain_len):
        line = ("{0:%d} " % max_domain_len).format(domain)
        if tls_policy.mode == "enforce":
            line += " secure match="
            line += ":".join(tls_policy.mxs)
        elif tls_policy.mode == "testing":
            line = "# " + line + "undefined due to testing policy"
        return line

    def _generate(self, policy_list):
        policies = []
        max_domain_len = len(max(policy_list, key=len))
        for domain, tls_policy in sorted(six.iteritems(policy_list)):
            policies.append(PostfixGenerator._policy_for_domain(domain, tls_policy, max_domain_len))
        file_contents = "\n".join(policies)
        self._write_config(file_contents, self._config_filename)

    def _generate_expired_fallback(self):
        file_contents = "# Policy list is outdated. Falling back to opportunistic encryption."
        self._write_config(file_contents, self._config_filename)

    def _instruct_string(self):
        filename = self._config_filename
        abs_path = os.path.abspath(filename)
        return ("\nFirst, run:\n\n"
            "postmap {abs_path}\n\n"
            "Then, you'll need to point your Postfix configuration to {filename}.\n"
            "Check if `postconf smtp_tls_policy_maps` includes this file.\n"
            "If not, run:\n\n"
            "postconf -e \"smtp_tls_policy_maps=$(postconf -h smtp_tls_policy_maps)"
            " hash:{abs_path}\"\n\n"
            "And finally:\n\n"
            "postfix reload\n").format(abs_path=abs_path, filename=filename)

    @property
    def mta_name(self):
        return "Postfix"

    @property
    def default_filename(self):
        return "postfix_tls_policy"

class EximGenerator(ConfigGenerator):
    """Configuration generator for exim.
    """

    def __init__(self, policy_dir):
        super(EximGenerator, self).__init__(policy_dir)
        self._host_config_filename = self._config_filename + ".host"
        self._domain_config_filename = self._config_filename + ".domain"

    @staticmethod
    def _policy_for_domain(domain, tls_policy, max_domain_len):
        line = ("{0:%d} " % (max_domain_len + 1)).format(domain + ":")
        if tls_policy.mode == "enforce":
            line += ":".join(tls_policy.mxs)
        elif tls_policy.mode == "testing":
            line = "# " + line + "undefined due to testing policy"
        return line

    def _generate(self, policy_list):
        policies = []
        hosts = set([])
        domains = set([])
        max_domain_len = len(max(policy_list, key=len))
        for domain, tls_policy in sorted(six.iteritems(policy_list)):
            policies.append(EximGenerator._policy_for_domain(domain, tls_policy, max_domain_len))
            hosts.update(tls_policy.mxs)
            domains.add(domain)
        self._write_config("\n".join(policies), self._config_filename)
        self._write_config("\n".join(hosts), self._host_config_filename)
        print("HI "  + self._domain_config_filename)
        self._write_config("\n".join(domains), self._domain_config_filename)

    def _generate_expired_fallback(self):
        file_contents = "# Policy list is outdated. Falling back to opportunistic encryption."
        self._write_config(file_contents, self._config_filename)
        self._write_config(file_contents, self._host_config_filename)
        self._write_config(file_contents, self._domain_config_filename)

    def _instruct_string(self):
        return ("\n1. Define the host and domain lists:\n"
            "\nhostlist enforce_tls_hosts = {hosts_listpath}\n"
            "domainlist enforce_tls_domains = {domains_listpath}\n"
            "\n2. Then define the following manual router before the dnslookup router:\n"
            "\ntlspolicy:\n"
            "    transport = remote_smtp\n"
            "    driver = manualroute\n"
            "    domains = +enforce_tls_domains\n"
            "    route_list = {route_listpath}\n"
            "    same_domain_copy_routing = yes\n"
            "    host_find_failed = ignore\n"
            "\n3. Set the following config options for the remote_smtp transport:\n"
            "\nhosts_require_tls = +enforce_tls_hosts\n"
            "tls_verify_hosts = +enforce_tls_hosts\n"
            "tls_verify_certificates = MAIN_TLS_VERIFY_CERTIFICATES\n"
            "\nThen restart exim.\n").format(
                domains_listpath=os.path.abspath(self._domain_config_filename),
                hosts_listpath=  os.path.abspath(self._host_config_filename),
                route_listpath=  os.path.abspath(self._config_filename))

    @property
    def mta_name(self):
        return "Exim"

    @property
    def default_filename(self):
        return "exim_tls_policy"
