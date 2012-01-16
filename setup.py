# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='GeekList Client Library',
    version='1.0',
    author='Julien Grenier',
    author_email='julien.grenier42@gmail.com',
    description='Library for accessing the GeekList API in Python',
    url='https//github.com/juliengrenier/python-geeklist',
    packages=['geeklist',''],
    license='MIT Licence',
    install_requires = ['oauth2', 'httplib2'],
    keywords=['geeklist', 'geekli.st', 'oauth']
)