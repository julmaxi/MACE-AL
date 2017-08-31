#!/usr/bin/env python

from setuptools import setup

setup(
    name='MACEAL',
    version='0.1',
    description='MACE active learning utility',
    author='Ines Rehbein',
    author_email='rehbein@cl.uni-heidelberg.de',
    packages=["maceal"],
    entry_points={
        'gui_scripts': ['mace-al = maceal.tkgui:main'],
    }
)
