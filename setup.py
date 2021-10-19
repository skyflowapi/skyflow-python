from setuptools import setup, find_packages

current_version = '1.0.0'

setup(
   name='skyflow',
   version=current_version,
   author='Skyflow',
   author_email='service-ops@skyflow.com',
   packages=find_packages(where='.', exclude=['test*']),
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
