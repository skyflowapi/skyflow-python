'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from setuptools import setup, find_packages
import sys


if sys.version_info < (3, 8):
    raise RuntimeError("skyflow requires Python 3.8+")
current_version = '2.0.0'

setup(
    name='skyflow',
    version=current_version,
    author='Skyflow',
    author_email='service-ops@skyflow.com',
    packages=find_packages(where='.', exclude=['test*']),
    url='https://github.com/skyflowapi/skyflow-python/',
    license='LICENSE',
    description='Skyflow SDK for the Python programming language',
    long_description=open('README.rst').read(),
    install_requires=[
        'python_dateutil >= 2.5.3',
    	'setuptools >= 21.0.0',
        'urllib3 >= 1.25.3, < 2.1.0',
        'pydantic >= 2',
        'typing-extensions >= 4.7.1',
        'DateTime~=5.5',
        'PyJWT~=2.9.0',
        'requests~=2.32.3',
        'coverage',
        'cryptography',
        'python-dotenv~=1.0.1',
        'httpx'
    ],
    python_requires=">=3.8",
)
