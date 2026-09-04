'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import os
import shutil
import sys

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py


if sys.version_info < (3, 9):
    raise RuntimeError("skyflow requires Python 3.9+")
current_version = '2.1.3.dev0+6098283'

HERE = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.dirname(HERE)
COMMON_SRC = os.path.join(REPO_ROOT, 'common')

with open(os.path.join(HERE, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()

# Anything under common/ that must never ride along into a built wheel.
_COMMON_EXCLUDE_DIRS = {'__pycache__', '.pytest_cache', 'tests', '.mypy_cache'}
_COMMON_EXCLUDE_FILES = {'setup.py', 'pyproject.toml', 'requirements.txt', '.gitignore'}
_COMMON_EXCLUDE_SUFFIXES = ('.egg-info',)


def _ignore_common_files(_directory, names):
    ignored = set()
    for name in names:
        if name in _COMMON_EXCLUDE_DIRS or name in _COMMON_EXCLUDE_FILES:
            ignored.add(name)
        elif name.endswith(_COMMON_EXCLUDE_SUFFIXES):
            ignored.add(name)
    return ignored


class CustomBuildPy(_build_py):
    """SK-2938 Option C: bundles the sibling common/ source tree into this variant's wheel
    (bdist_wheel/build --wheel only -- sdist doesn't invoke this and isn't supported here)."""

    def run(self):
        super().run()
        dest = os.path.join(self.build_lib, 'common')
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(COMMON_SRC, dest, ignore=_ignore_common_files)


setup(
    name='skyflow',
    version=current_version,
    author='Skyflow',
    author_email='service-ops@skyflow.com',
    packages=find_packages(where='.', exclude=['test*', 'samples*']),
    # Ship PEP 561 markers so type checkers (mypy/pyright) see the SDK's types.
    package_data={
        'skyflow': ['py.typed'],
        'skyflow.generated.rest': ['py.typed'],
    },
    cmdclass={'build_py': CustomBuildPy},
    url='https://github.com/skyflowapi/skyflow-python/',
    license='LICENSE',
    description='Skyflow SDK for the Python programming language',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'pydantic >= 2.0.0',
        'typing-extensions >= 4.0.0',
        'PyJWT >= 2.12, < 3',
        'requests >= 2.28.0',
        'cryptography >= 44.0.2',
        'httpx >= 0.21.2',
        'python-dotenv >= 1.1.0, < 2',
    ],
    extras_require={
        'dev': [
            'codespell >= 2.4.1',
            'ruff >= 0.9.0',
            'pre-commit >= 4.3.0',
            'griffe == 2.2.0; python_version >= "3.10"',
        ]
    },
    python_requires=">=3.9",
)
