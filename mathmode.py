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


def array_mathmode(s):
    def _array_math_display(s):
        s = re.sub(
            ur'\\begin\s?{array}[\s\S]*?\\end\s?{array}', lambda x: ur'\[%s\]' % x.group(), s)
        return s

    def _dealdisplay(s):
        stop = s.find(ur'\]')
        if stop == -1:
            s = _array_math_display(s)
        else:
            math = s[:stop]
            text = s[stop:]
            text = _array_math_display(text)
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
            math = s[:stop]
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


def cn_in_mathmode(s):  # by ningshuo

    def _deal_mathmode(s):
        s = re.sub(ur'[\u4e00-\u9fa5]+',
                   lambda x: ur'\text{%s}' % x.group(), s)
        return s

    def _deal_textmode(s):

        s = s.replace(u'\n', u'\\\\\n')

        return s

    def _dealdisplay(s):
        stop = s.find(ur'\]')
        if stop == -1:
            s = _deal_textmode(s)
        else:
            math = s[:stop]
            math = _deal_mathmode(math)
            text = s[stop:]
            text = _deal_textmode(text)
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
            math = s[:stop]
            math = _deal_mathmode(math)
            k = s[stop:]
            k = re.split(ur'(?<!\\)\\\[', k)
            for idx, str in enumerate(k, start=0):
                k[idx] = _dealdisplay(str)
            k = ur'\['.join(k)
            s = math + k
        return s

    s = array_mathmode(s)
    s = re.split(ur'(?<!\\)\\\(', s)
    for idx, str in enumerate(s, start=0):
        s[idx] = _dealinline(str)
    s = ur'\('.join(s)
    s = s.replace(u'\\\\\n\[', u'\n\[')
    s = s.replace(u'\]\\\\\n', u'\]\n')
    return s

s = ur'''为了在实验中保护电流表和调节电阻时电压表、电流表的示数变化均明显，乙同学对甲同学的实验进行改进，设计了如图丙所示的电路，丙电路中电阻  \( R_{0} \)  应该选取下列备选电阻的哪一个？         \\
A.  \(  1\ \Omega     \)  B.  \(  5 \ \Omega     \)  C.  \(  10\ \Omega     \)  D.  \(  20\ \Omega    \) 
是么'''

re_choice = re.compile(ur'(A\..*?)(B\..*?)(C\..*?)(D\.[^\n]*)')
# print re.findall(re_choice, s)


# def deal_choice(x):
# print x.group(1)
# x = re.sub(re_choice, deal_choice, s)

print re.sub(ur'.*?([\u4e00-\u9fa5]+).*?', lambda x: x.group(1), s)
