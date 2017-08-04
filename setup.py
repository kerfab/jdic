from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(

    name='sample',
    version='1.0.0',
    description='Jdic facilitates manipulation of Json-like objects',
    long_description=long_description,
    url='https://github.com/kerfab/jdic/',
    author='Fabien Kerbouci',
    author_email='fkerbouci@gmail.com',
    license='Unlicense',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: Unlicense License',

        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],

    keywords='json dict path diff match',

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    install_requires=['mongoquery', 'json_delta', 'jsonschema', 'jsonpath_ng'],

    extras_require={},

    package_data={},

    data_files=[],

    entry_points={}
)
