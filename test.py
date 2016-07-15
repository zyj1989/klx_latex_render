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

s = [
    '543de2db0045fe487b37ec91',
    '56f7bf365417d175d07512f5',
    '56f9f8965417d175d1751ba0',
    '57255b90def2970e65c995a5',
    '5747ab45def29749c8c72a1e',
    '5747b089def29749c8c72a7e',
    '57482ea4def29749c8c730f7',
    '543de2db0045fe487b37ec91',
    '543de2db0045fe487b37ec91',
    '543de2db0045fe487b37ec91',
    '543de2db0045fe487b37ec91',
    '543de2db0045fe487b37ec91',
    '543de2db0045fe487b37ec91',
    '56f7bf365417d175d07512f5',
    '56f7bf365417d175d07512f5',
    '56f7bf365417d175d07512f5',
    '56f7bf365417d175d07512f5',
    '56f7bf365417d175d07512f5',
    '56f7bf365417d175d07512f5',
    '56f9f8965417d175d1751ba0',
    '56f9f8965417d175d1751ba0',
    '56f9f8965417d175d1751ba0',
    '56f9f8965417d175d1751ba0',
    '56f9f8965417d175d1751ba0',
    '56f9f8965417d175d1751ba0',
    '57255b90def2970e65c995a5',
    '57255b90def2970e65c995a5',
    '57255b90def2970e65c995a5',
    '57255b90def2970e65c995a5',
    '57255b90def2970e65c995a5',
    '57255b90def2970e65c995a5',
    '57346fcbdef297350e03ca2e',
    '57346fcbdef297350e03ca2e',
    '57346fcbdef297350e03ca2e',
    '573e9d06def2977016b059da',
    '573e9d06def2977016b059da',
    '573e9d06def2977016b059da',
    '5747ab45def29749c8c72a1e',
    '5747ab45def29749c8c72a1e',
    '5747ab45def29749c8c72a1e',
    '5747ab45def29749c8c72a1e',
    '5747ab45def29749c8c72a1e',
    '5747ab45def29749c8c72a1e',
    '5747b089def29749c8c72a7e',
    '5747b089def29749c8c72a7e',
    '5747b089def29749c8c72a7e',
    '5747b089def29749c8c72a7e',
    '5747b089def29749c8c72a7e',
    '5747b089def29749c8c72a7e',
    '57482ea4def29749c8c730f7',
    '57482ea4def29749c8c730f7',
    '57482ea4def29749c8c730f7',
    '57482ea4def29749c8c730f7',
    '57482ea4def29749c8c730f7',
    '57482ea4def29749c8c730f7', ]

print set(s)
