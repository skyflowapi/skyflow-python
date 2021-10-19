from setuptools import setup, find_packages

version = '1.0.0'

setup(
   name='skyflow',
   version=version,
   author='Skyflow',
   author_email='service-ops@skyflow.com',
   packages=find_packages(exclude=['tests', 'examples']),
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
