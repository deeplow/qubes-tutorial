#!/usr/bin/env python3
''' Setup.py file '''
import os
import setuptools

def read_file(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()

setuptools.setup(
    name='qubes-tutorial',
    version=read_file('version')[:-1], # remove trailing new line
    author='deeplow',
    author_email='deeplower at protonmail.com',
    description='Qubes Integrated Tutorial Package',
    license='GPL2+',
    url='https://github.com/deeplow',
    keywords='integrated qubes tutorial',
    long_description=read_file('README.md'),
    packages=("qubes_tutorial",
              "qubes_tutorial.gui",
              "qubes_tutorial.tests",
              "qubes_tutorial.included_tutorials.onboarding"),
    package_data = {
            'qubes_tutorial.gui': ['*.ui', 'images/*'],
            'qubes_tutorial.included_tutorials.onboarding': ['*.ui','images/*']
    },
    entry_points={
        'console_scripts': [
            'qubes-tutorial = qubes_tutorial.tutorial:main'
        ]
    }
)
