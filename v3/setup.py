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
current_version = '1.0.0'

HERE = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.dirname(HERE)
COMMON_SRC = os.path.join(REPO_ROOT, 'common')

with open(os.path.join(REPO_ROOT, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()

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
    """SK-2938 Option C bundling mechanism -- see v2/setup.py for full rationale. Bundles the
    sibling common/ source tree into this variant's wheel; wheel builds only, not sdist."""

    def run(self):
        super().run()
        dest = os.path.join(self.build_lib, 'common')
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(COMMON_SRC, dest, ignore=_ignore_common_files)


setup(
    name='skyflow-flowvault',
    version=current_version,
    author='Skyflow',
    author_email='service-ops@skyflow.com',
    packages=find_packages(where='.', exclude=['test*', 'samples*']),
    package_data={
        'skyflow': ['py.typed'],
        'skyflow.generated.rest': ['py.typed'],
    },
    cmdclass={'build_py': CustomBuildPy},
    url='https://github.com/skyflowapi/skyflow-python/',
    license='LICENSE',
    description='Skyflow SDK for the Python programming language (v3 / flowservice API)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'pydantic >= 2.0.0',
        'typing-extensions >= 4.0.0',
        'PyJWT >= 2.12, < 3',
        'cryptography >= 44.0.2',
        'httpx >= 0.21.2',
        'python-dotenv >= 1.1.0, < 2',
        # NOTE: 'requests' intentionally omitted -- only used today by v2's Connection
        # controller, which isn't part of v3's scope this round.
    ],
    extras_require={
        'dev': [
            'codespell >= 2.4.1',
            'ruff >= 0.9.0',
            'pre-commit >= 4.3.0',
        ]
    },
    python_requires=">=3.9",
)
