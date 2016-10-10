import os
import re
from setuptools import setup, find_packages

# reading the package version without loading the package.
with open(os.path.join(os.path.dirname(__file__), 'sqlalchemy_media', '__init__.py')) as v_file:
    package_version = re.compile(r".*__version__ = '(.*?)'", re.S).match(v_file.read()).group(1)

dependencies = [
    'sqlalchemy >= 1.1.0b3',
]


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name="sqlalchemy-media",
    version=package_version,
    author="Vahid Mardani",
    author_email="vahid.mardani@gmail.com",
    url="http://sqlalchemy-media.dobisel.com",
    description="Sqlalchemy asset manager",
    maintainer="Vahid Mardani",
    maintainer_email="vahid.mardani@gmail.com",
    packages=find_packages(),
    platforms=["any"],
    long_description=read('README.rst'),
    install_requires=dependencies,
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries'
    ],
)
