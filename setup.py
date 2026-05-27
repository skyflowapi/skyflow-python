'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from setuptools import setup, find_packages
import sys

if sys.version_info < (3, 7):
    raise RuntimeError("skyflow requires Python 3.7+")
current_version = '2.1.1.dev0+3520034'

setup(
    name='skyflow',
    version=current_version,
    author='Skyflow',
    author_email='service-ops@skyflow.com',
    packages=find_packages(where='.', exclude=['test*']),
    url='https://github.com/skyflowapi/skyflow-python/',
    license='LICENSE',
    description='[DEPRECATED - EOL 2026-10-31] Skyflow Python SDK v1.x. Migrate to v2: https://github.com/skyflowapi/skyflow-python/blob/main/docs/migrate_to_v2.md',
    long_description=open('README.rst').read(),
    install_requires=[
        'PyJWT',
        'datetime',
        'requests',
        'aiohttp',
        'asyncio',
        'cryptography>=3.3.1'
    ],
    python_requires=">=3.7"
)
