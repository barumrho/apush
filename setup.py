# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='apush',
    version='0.0.1',
    description='A simple Apple push notification service provider',
    long_description=readme,
    author='Barum Rho',
    author_email='barum@barumrho.com',
    url='https://github.com/barumrho/apush',
    license=license,
    keywords='apple push notification',
    py_modules=['apush']
)

