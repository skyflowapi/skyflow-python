from setuptools import setup, find_packages
import sys

if sys.version_info < (3, 7):
    raise RuntimeError("skyflow requires Python 3.7+")
current_version = '1.2.1'

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
       'PyJWT',
       'datetime',
       'requests',
       'aiohttp',
       'asyncio',
       'cryptography>=3.3.1'
   ],
   python_requires=">=3.7"
)
