# -*- coding: utf-8 -*-

import codecs
import os
import re
import sys
from setuptools import setup

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def read(*parts):
    return codecs.open(os.path.join(os.path.dirname(__file__), *parts),
                       encoding='utf8').read()


try:
    bytes
except NameError:
    bytes = str


class UltraMagicString(object):
    '''
    Taken from
    http://stackoverflow.com/questions/1162338/whats-the-right-way-to-use-unicode-metadata-in-setup-py
    '''
    def __init__(self, value):
        if not isinstance(value, bytes):
            value = value.encode('utf8')
        self.value = value

    def __bytes__(self):
        return self.value

    def __unicode__(self):
        return self.value.decode('UTF-8')

    if sys.version_info[0] < 3:
        __str__ = __bytes__
    else:
        __str__ = __unicode__

    def __add__(self, other):
        return UltraMagicString(self.value + bytes(other))

    def split(self, *args, **kw):
        return str(self).split(*args, **kw)


long_description = UltraMagicString('\n\n'.join((
    read('README.rst'),
#     read('CHANGES.rst'),
)))

package_name = 'midict'

setup(
    name=package_name,
    version=find_version(package_name, '__init__.py'),
    url='https://github.com/ShenggaoZhu/midict',
#    download_url = 'https://codeload.github.com/ShenggaoZhu/midict/zip/v0.1.1',
    license='MIT',
    description=
        'MIDict (Multi-Index Dict) can be indexed by any "keys" or "values", suitable as a '
        'bidirectional/inverse dict or a multi-key/multi-value dict (a drop-in replacement '
        'for dict in Python 2 & 3).',
    long_description=long_description,
    author=UltraMagicString('Shenggao Zhu'),
    author_email='zshgao@gmail.com',
    packages=[package_name],
    include_package_data=True,
    zip_safe=True,
    keywords = 'dict, dictionary, mapping, bidirectional, bijective, two-way, double, inverse, reverse, '
        'multiple, index, multiple indices, multiple values, multiple keys, MIMapping, MIDict, FrozenMIDict, '
        'AttrDict, IndexDict, multi-indexing syntax',
    install_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],

)