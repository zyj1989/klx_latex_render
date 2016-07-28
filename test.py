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


def unicode_chem_cor(ori):
    ori = re.sub(ur'\s*?}', ur'}', ori)
    ori = re.sub(ur'(?<!(?:-|=))>', lambda x: ur'\gt', ori)
    ori = re.sub(ur'<(?!(?:-|=))', lambda x: ur'\lt', ori)
    return ori

a = u'<= 123123 => asda < asda> '
print unicode_chem_cor(a)
