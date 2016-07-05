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
import cStringIO
from PIL import Image


file = open('../imgs/4dfe127f2dc9a166d85af7f332710d94.png')
tmp_img = cStringIO.StringIO(file.read())
im = Image.open(tmp_img)
print im.format, im.size, im.mode
