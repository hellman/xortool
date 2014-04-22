#!/usr/bin/env python
#-*- coding:utf-8 -*-

from distutils.core import setup

setup(name='xortool',
      version='1.0',
      description='Tool for xor cipher analysis',

      author='hellman',
      author_email='hellman1908@gmail.com',
      license="MIT",

      url='https://github.com/hellman/xortool',
      packages=['xortool'],
      scripts=["xortool/xortool", "xortool/xortool-xor"]
      )
