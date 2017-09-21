from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='jdic',
    version=read_file("VERSION.txt"),
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Utilities"
    ],
    author='Fabien Kerbouci',
    description="A ready-to-use library which eases the manipulation "
                "of JSON-like documents, so that you can focus on "
                "logic instead of losing time in formal document manipulations."
                "Jdic offers original features, but also embeds mission-critical " 
                "3rd party libraries and unite them all within a comprehensive "
                "easy-to-use API."
    long_description=README,
    author_email='',
    url='https://github.com/kerfab/jdic',
    keywords='jdic json checksum diff patch find match mongo mongodb path',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False
)
