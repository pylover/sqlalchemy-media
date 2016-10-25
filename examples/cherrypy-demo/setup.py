
import os
import re
from setuptools import setup, find_packages

# reading the package version without loading the package.
with open(os.path.join(os.path.dirname(__file__), 'cp_sam', '__init__.py')) as v_file:
    package_version = re.compile(r".*__version__ = '(.*?)'", re.S).match(v_file.read()).group(1)

dependencies = [
    'cherrypy',
    'sqlalchemy-media',
]


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name="cp_sam",
    version=package_version,
    packages=find_packages(),
    install_requires=dependencies,
)
