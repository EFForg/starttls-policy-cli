import sys

from setuptools import setup
from setuptools import find_packages
from os import path

version = '0.0.1.dev0'

install_requires = [
    'datetime',
    'python-dateutil',
    'setuptools',
    'six',
]

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), 'rb') as f:
    long_description = f.read().decode('utf-8-sig')

setup(
    name='starttls_policy_cli',
    version=version,
    description="Policy API for STARTTLS Preload",
    url='https://github.com/EFForg/starttls-everywhere',
    author="Sydney Li",
    author_email='sydney@eff.org',
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Communications :: Email :: Mail Transport Agents',
        'Topic :: Security',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],

    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'dev': [
            'coverage',
            'mock',
            'pylint',
            'pytest',
            'pytest-cov',
            # Requirements for proper packing of markdown description:
            'setuptools>=38.6.0',
            'wheel>=0.31.0',
            'twine>=1.11.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'starttls-policy-cli = starttls_policy_cli.main:main',
        ],
    },
    long_description=long_description,
    long_description_content_type='text/markdown'
)

