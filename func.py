#!/usr/bin/env python
# encoding:utf-8
'''
自用函数库
'''
import time
import sys
import copy
import hashlib
import numpy as np
import logging
import pandas as pd
from bson.objectid import ObjectId
from pymongo import MongoClient
from pandas import DataFrame
reload(sys)
sys.setdefaultencoding('utf-8')
client = MongoClient('10.0.0.100', 27017)


def combined(val):
    """
    判断val是不是dict或者list
    :param val:
    :return: none
    """
    if isinstance(val, list) or isinstance(val, dict):
        return True
    return False


def encode_object(val):
    """
    Object2str
    :param val:
    :return:
    """
    ans = val
    if isinstance(ans, ObjectId):
        tid = str(ans)
        ans = 'ObjectId:' + tid
    return ans


def decode_object(val):
    """
    str2Object
    :param val:
    :return:
    """
    ans = val
    if isinstance(ans, str) or isinstance(ans, unicode):
        res = re.search(r'^(ObjectId:)([0-9a-fA-F]+)', ans)
        if res:
            ans = ObjectId(res.group(2))
    return ans


def show_pretty_dict(val, deep=0):
    """
    格式化输出，用来调试
    :param val:
    :param deep:
    :return: None
    """
    if isinstance(val, dict):
        for r in val:
            if combined(val[r]):
                # print '\t' * deep, r
                tb = u'\t' * deep
                tb += unicode(r)
                tb += u' : '
                # logging.info(tb)
                print tb
                show_pretty_dict(val[r], deep + 1)
            else:
                # print '\t' * deep, r, val[r]
                tb = u'\t' * deep
                tb += unicode(r)
                tb += u' : '
                tb += unicode(val[r])
                # logging.info(tb)
                print tb
    elif isinstance(val, list):
        for i, r in enumerate(val):

            if combined(val[i]):
                # print '\t' * deep, i
                tb = u'\t' * deep
                tb += unicode(i)
                tb += u' : '
                # logging.info(tb)
                print tb
                show_pretty_dict(val[i], deep + 1)
            else:
                # print '\t' * deep, i, val[i]
                tb = u'\t' * deep
                tb += unicode(i)
                tb += u' : '
                tb += unicode(val[i])
                # logging.info(tb)
                print tb

    else:
        # print '\t' * deep, val
        tb = u'\t' * deep
        tb += u' : '
        tb += unicode(val)
        # logging.info(tb)
        print tb


def get_items(volume_id, dbname):
    # dbname = 'physics'
    db = client[dbname]

    raw_q_ids = db.volume.find_one({'_id': ObjectId(volume_id)})['raw_q_ids']

    parsed_q_ids = []
    for i in raw_q_ids:
        a = db.parsed_q.find({'raw_q_id': i})
        for j in a:
            parsed_q_ids.append(j['_id'])

    item_ids = []
    item_list = {}
    for i in parsed_q_ids:
        b = db.item.find({'parsed_q_id': i})
        for j in b:
            item_ids.append(j['_id'])
    return item_ids


def get_volume_name(volume_id, dbname):
    db = client[dbname]
    for a in db.volume.find({'_id': ObjectId(volume_id)}, {'name': 1}):
        volume_name = a['name']
    return volume_name


def get_children(tag_id, dbname, a):
    db = client[dbname]
    child1_list = []
    child2_list = []
    child3_list = []
    child1_name = []
    child2_name = []
    child3_name = []
    self_name = []
    self = [ObjectId(tag_id)]
    tags = db.knowledge_tags.find({'_id': ObjectId(tag_id)})
    for tag in tags:
        self_name.append(tag['name'])
    child1s = db.knowledge_tags.find(
        {'deleted': False, 'parent': ObjectId(tag_id)})
    for child1 in child1s:
        child1_list.append(child1['_id'])
        child1_name.append(child1['name'])
    child2s = db.knowledge_tags.find(
        {'deleted': False, 'parent': {'$in': child1_list}})
    for child2 in child2s:
        child2_list.append(child2['_id'])
        child2_name.append(child2['name'])
    child3s = db.knowledge_tags.find(
        {'deleted': False, 'parent': {'$in': child2_list}})
    for child3 in child3s:
        child3_list.append(child3['_id'])
        child3_name.append(child3['name'])

    children_list = self + child1_list + child3_list + child2_list
    children_name_list = self_name + child1_name + child2_name + child3_name
    if a == 1:
        return children_name_list
    else:
        return children_list


def get_tag_name(tag_id, dbname):
    db = client[dbname]
    a = db.knowledge_tags.find({'_id': ObjectId(tag_id)})
    for x in a:
        b = x['name']
    return b


def get_ctime(a):
    return time.mktime(time.strptime(a, '%Y-%m-%d %H:%M:%S'))


def let_valid(a):
    if a == None:
        return 0
    else:
        return a


def get_school_info_id(school_name):
    db = client['enjoystudy']
    for school_info in db.school_info.find({'name': school_name}):
        return school_info['_id']


def calculate_paper_md5(paper):
    content = u''
    for part in paper['parts']:
        for item in part:
            content += str(item['item_id'])
            for sub_q in item['sub_q']:
                content += str(sub_q)
    return hashlib.md5(content).hexdigest()


def get_school_teachers_username(school_name):
    db = client['enjoystudy']
    teachers_username = {}
    for teacher in db.users.find({'school': school_name, 'role': 1}):
        teachers_username[teacher['username']] = teacher['name']
    return teachers_username
