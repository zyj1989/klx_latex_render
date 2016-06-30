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

s = '\n[[img]]{\"src\": \"7b126a54e029a827a0dbda337c0dea09.png\", \"width\": \"183\"}[[/img]]'
re_img = re.compile(ur'\n?\[\[img\]\].*?\[\[/img\]\]')
s = re.sub(re_img, 'xxx', s)

print s
