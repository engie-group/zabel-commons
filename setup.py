# Copyright (c) 2020 Martin Lafaix (martin.lafaix@external.engie.com)
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0

from setuptools import setup, find_namespace_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='zabel-commons',
    version='1.7.0',
    description='The Zabel transverse **commons** library',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/engie-group/zabel',
    author='Martin Lafaix',
    author_email='martin.lafaix@external.engie.com',
    license='Eclipse Public License 2.0',
    packages=find_namespace_packages(include=['zabel.*']),
    install_requires=['requests>=2.32'],
    extras_require={'bottle': ['bottle>=0.12.25'], 'all': ['bottle>=0.12.25']},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)',
        'Operating System :: OS Independent',
        'Topic :: Utilities',
    ],
    python_requires='>= 3.8.0',
)
