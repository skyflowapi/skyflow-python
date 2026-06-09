'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from setuptools import setup, find_packages
import sys


if sys.version_info < (3, 9):
    raise RuntimeError("skyflow requires Python 3.9+")
current_version = '2.1.1'

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
        'python_dateutil >= 2.5.3',
    	'setuptools >= 75.3.3',
        'urllib3 >= 1.25.3, < 3',
        'pydantic >= 2',
        'typing-extensions >= 4.7.1',
        'DateTime~=5.5',
        'PyJWT >= 2.12, < 3',
        'requests~=2.32.3',
        'coverage',
        'cryptography',
        'python-dotenv >= 1.0, < 2',
        'httpx'
    ],
    extras_require={
        'dev': [
            'codespell',
            'ruff'
        ]
    },
    python_requires=">=3.9",
)
