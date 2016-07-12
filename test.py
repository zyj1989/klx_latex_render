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

template = ur'''% !TEX encoding=utf8
% !TEX program=xelatex
\documentclass{klx}
\begin{document}
'''
s = ur'print（\% io%（2），A）'
a = re.findall(ur'(?<!(?:\\|%))%', s)
b = re.sub(ur'(?<!(?:\\|%))%', 'xxxx', s)
print b
