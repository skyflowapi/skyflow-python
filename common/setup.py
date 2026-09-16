'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from setuptools import setup, find_packages

setup(
    # Never published to PyPI -- bundled into the v2/v3 wheels at build time (see their
    # setup.py CustomBuildPy). Exists for local dev (`pip install -e ./common`) and tests/contract/.
    name='skyflow-common',
    version='0.0.0',
    author='Skyflow',
    author_email='service-ops@skyflow.com',
    description='Internal shared code for the Skyflow Python SDK v2/v3 build variants. Not published independently.',
    packages=find_packages(where='.', exclude=['tests*']),
    package_data={
        'common.generated.rest': ['py.typed'],
    },
    install_requires=[
        'pydantic >= 2.0.0',
        'typing-extensions >= 4.0.0',
        'PyJWT >= 2.12, < 3',
        'cryptography >= 44.0.2',
        'httpx >= 0.21.2',
        'python-dotenv >= 1.1.0, < 2',
    ],
    python_requires=">=3.9",
)
