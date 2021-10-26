from setuptools import setup, find_packages

current_version = '1.0.1'

setup(
   name='skyflow',
   version=current_version,
   author='Skyflow',
   author_email='service-ops@skyflow.com',
   packages=find_packages(where='.', exclude=['test*']),
   url='https://github.com/skyflowapi/skyflow-python/',
   license='LICENSE',
   description='Skyflow SDK for the Python programming language',
   long_description=open('INFO.rst').read(),
   install_requires=[
       'PyJWT',
       'datetime',
       'requests',
       'cryptography>=3.3.1'
   ],
)
