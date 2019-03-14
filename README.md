# starttls-policy-cli Python package

Run `pip install starttls_policy_cli` to install!

### Generating a configuration file

`starttls-policy-cli --generate <MTA> [--policy-dir /path/to/dir]` will generate a configuration file corresponding to the TLS policy list and provide instructions for installing the file.

We currently only support Postfix, but contributions are welcome!

#### Early adopter mode

The flag `--early-adopter` (or `-e`) processes all "testing" domains in the policy list the same way as domains in "enforce" mode, effectively requiring strong TLS for all domains. This mode is useful for participating in tests of recently added domains and stronger security hardening at the cost of increased probability of delivery degradation.

## Development

We recommend using `virtualenv` and `pip` to install and run `starttls-policy-cli` while developing. To get set up:
```
virtualenv --no-site-packages --setuptools starttls_venv --python python3.6
source ./starttls_venv/bin/activate
pip install -e .
```
