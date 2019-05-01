# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

"""Setup for package django-os2webscanner."""

import os
import pathlib

from setuptools import setup

basedir = pathlib.Path(__file__).absolute().parent
readme_text = basedir.joinpath('README').read_text()

requires = basedir.joinpath('doc', 'requirements.txt').read_text().split()

# allow setup.py to be run from any path
os.chdir(str(basedir))

setup(
    name='os2datascanner',
    version='1.0',
    package_dir={'': 'src'},
    packages=['os2webscanner', 'webscanner', 'scraping'],
    include_package_data=True,
    license='MPL',  # example license
    description='OS2Webscanner for Danish municipalities',
    long_description=readme_text,
    url='http:///magenta.dk',
    author='Magenta ApS',
    author_email='os2webscanner@magenta.dk',
    setup_requires=['setuptools'],
    install_requires=requires,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # replace these appropriately if you are using Python 3
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
