#!/usr/bin/env python
# encoding:utf-8
'''
试卷渲染
'''
import re
import time
import sys
import os
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('..')
import copy
import logging
import urllib2
from bson.objectid import ObjectId
from pymongo import MongoClient


def times(x):
    return x * 3


def test(x, f):
    def f(x):
        return x + 5
    return times(f(x))


def f(x):
    return x + 1

print test(1, f)
