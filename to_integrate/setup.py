'''
setup.py

installation script

'''

from setuptools import setup

setup(name='nfl',
      version='0.1',
      description='python library for scraping football data',
      url='http://github.com/sansbacon/nfl',
      author='Eric Truett',
      author_email='eric@erictruett.com',
      license='MIT',
      packages=['nfl'],
      zip_safe=False)
