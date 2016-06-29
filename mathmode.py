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


def cn_in_mathmode(s):  # by ningshuo
    def _dealdisplay(s):
        stop = s.find(ur'\]')
        if stop == -1:
            s = s.replace(u'\n', u'\\\\\n')
        else:
            math = re.sub(ur'[\u4e00-\u9fa5]+',
                          lambda x: ur'\text{%s}' % x.group(), s[:stop])
            text = s[stop:]
            s = math + text
        return s

    def _dealinline(s):
        stop = s.find(ur'\)')
        if stop == -1:
            s = re.split(ur'(?<!\\)\\\[', s)
            for idx, str in enumerate(s, start=0):
                s[idx] = _dealdisplay(str)
            s = ur'\['.join(s)
        else:
            math = re.sub(ur'[\u4e00-\u9fa5]+',
                          lambda x: ur'\text{%s}' % x.group(), s[:stop])
            k = s[stop:]
            k = re.split(ur'(?<!\\)\\\[', k)
            for idx, str in enumerate(k, start=0):
                k[idx] = _dealdisplay(str)
            k = ur'\['.join(k)
            s = math + k
        return s

    s = re.split(ur'(?<!\\)\\\(', s)
    for idx, str in enumerate(s, start=0):
        s[idx] = _dealinline(str)
    s = ur'\('.join(s)
    return s

s = ur'''\(深海探测 \dfrac12\)c.温度是描述热运动的物理量，一个系统与另一个系统达到热平衡时两系统温度相同
d.物体由大量分子组成，其单个分子的运动是无规则的，
大量分子的运动也是无规律的
\[\begin{array}{ccc}
1&2&3\\\hline
&&中文\\\hline\]'''


print cn_in_mathmode(s)
