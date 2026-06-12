'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from setuptools import setup, find_packages
import sys


if sys.version_info < (3, 9):
    raise RuntimeError("skyflow requires Python 3.9+")
current_version = '1.16.1.dev0+ce540c1'

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='skyflow',
    version=current_version,
    author='Skyflow',
    author_email='service-ops@skyflow.com',
    packages=find_packages(where='.', exclude=['test*']),
    # Ship PEP 561 markers so type checkers (mypy/pyright) see the SDK's types.
    package_data={
        'skyflow': ['py.typed'],
        'skyflow.generated.rest': ['py.typed'],
    },
    url='https://github.com/skyflowapi/skyflow-python/',
    license='LICENSE',
    description='Skyflow SDK for the Python programming language',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'pydantic >= 2.0.0',
        'typing-extensions >= 4.0.0',
        'PyJWT >= 2.12, < 3',
        'requests >= 2.32.2',
        'cryptography >= 44.0.2',
        'httpx >= 0.21.2',
        'python-dotenv >= 1.1.0, < 2',
    ],
    extras_require={
        'dev': [
            'codespell >= 2.4.1',
            'ruff >= 0.9.0',
            'pre-commit >= 4.3.0',
        ]
    },
    python_requires=">=3.9",
)
