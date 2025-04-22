#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="ailand",
    version="0.1.2",
    packages=find_packages(include=['ailand', 'ailand.*']),
    install_requires=[
        'pytz>=2024.1',
        'pymysql>=1.1.1',
        'rainbow_logging_handler>=2.1.0',
    ],
    author="Young Park",
    author_email="young.park@gmail.com",
    description="A short description of my utility",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    # url="https://github.com/yourusername/my_package",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: HIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)