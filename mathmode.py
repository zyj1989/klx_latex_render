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

s = ur'''某同学在研究性学习中记录了一些与地球、月球有关的数据资料如图中表所示，利用这些数据来计算地球表面与月球表面之间的距离  \( {\rm s} \) ，则下列运算公式中错误的是（）
\begin{array}{|c|c|} \hline
地球半径&R=6400\ {\rm km}\\  \hline
月球半径&r=1740\ {\rm km}\\  \hline
地球表面重力加速度&g0=9.80\ \rm{m/s^2}\\  \hline
月球表面重力加速度&g'=1.56\ \rm{m/s^2}\\  \hline
月球绕地球转动的线速度&v=1\ {\rm km/s}\\  \hline
月球绕地球转动周期&T=27.3天\\  \hline
光速&c=2.998 \times 10^5 \ {\rm km/s}\\  \hline
用激光器向月球表面发射激光光束,经过约t=2.565\ {\rm s}接收到从月球表面反射回来的激光信号\\  \hline
\end{array}'''

print array_mathmode(s)
