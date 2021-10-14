from setuptools import setup

setup(
   name='Skyflow',
   version='1.0.0',
   author='Skyflow Python SDK',
   author_email='service-ops@gmail.com',
   packages=['ServiceAccount'],
   url='http://pypi.python.org/pypi/PackageName/',
   license='LICENSE',
   description='An awesome package that does something',
   long_description=open('README.md').read(),
   install_requires=[
       'PyJWT',
       'datetime',
       'requests'
   ],
)
