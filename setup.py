from setuptools import setup

version = '1.0.0'

setup(
   name='Skyflow',
   version=version,
   author='Skyflow',
   author_email='service-ops@skyflow.com',
   packages=['skyflow'],
   url='https://github.com/skyflowapi/skyflow-python/',
   license='LICENSE',
   description='Skyflow SDK for the Python programming language',
   long_description=open('README.md').read(),
   install_requires=[
       'PyJWT',
       'datetime',
       'requests'
   ],
)
