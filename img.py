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
client = MongoClient('10.0.0.100', 27017)
dbname = 'klx_math'
db = client[dbname]


subject = dbname
paper_path = '../papers'
item_path = '../items'
# img_path = '../imgs/'
img_path = '/Users/zhangyingjie/var/data/img'
template = ur'''% !TEX encoding=utf8
% !TEX program=xelatex
\documentclass{klxp}'''
template += ur'''
\graphicspath{{%s/}}
\begin{document}
''' % img_path

# img_re2 = re.compile(ur'\n\[\[img\]\].*?\[\[/img\]\]')
img_re2 = re.compile(ur'\[\[img\]\].*?\[\[/img\]\]')  # used for desc imgs
# used for delete imgs urls
img_re3 = re.compile(
    ur'\n?\s?\u200b?(\[\[img\]\].*?\[\[/img\]\])\u200b?\s?\n?')
img_re4 = re.compile(ur'\[\[img\]\].*?\[\[/img\]\]\u200b?\s?\n')
img_file_re = re.compile(ur'\w+\.(?:png|jpg|gif|bmp|jpeg|tif)')
img_display_pattern = re.compile(ur'\[\[display\]\](.*?)\[\[/display\]\]')
img_inpar_pattern = re.compile(ur'\[\[inpar\]\](.*?)\[\[/inpar\]\]')
img_inline_pattern = re.compile(ur'\[\[inline\]\](.*?)\[\[/inline\]\]')


def str2latex(ori):
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
            latex_remaining_char = ['$', '%', '&', '#', '^', '_', ]
            s = s.replace(u'\n', u'\\\\{}\n')
            # for k in latex_remaining_char:
            s = re.sub(ur'(?<!\\)\$', u'\\$', s)
            s = re.sub(ur'(?<!\\)%', u'\\%', s)
            s = re.sub(ur'(?<!\\)&', u'\\&', s)
            s = re.sub(ur'(?<!\\)#', u'\\#', s)
            s = re.sub(ur'(?<!\\)\^', u'\\^', s)
            s = re.sub(ur'(?<!\\)_', u'\\_', s)
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

    def array_col_correction(x):
        x.group(0).split('\\\\')[0]
        col_num = len(re.findall(ur'(?<!\\)&', x.group(0).split('\\\\')[0]
                                 )) + 1
        col_arg_center = 'c' * col_num
        col_arg_left = 'l' * col_num
        col_arg_lined = ur'|' + ur'c|' * col_num
        s = re.sub(ur'{c+}', '{%s}' % col_arg_center, x.group(0))
        s = re.sub(ur'{\|c\|.*?}', '{%s}' % col_arg_lined, s)
        s = re.sub(ur'{l+}', '{%s}' % col_arg_left, s)
        return s

    def split_mathmode(x):
        x = re.sub(ur'split', ur'aligned', x.group(0))
        return x

    def unicode_2_latex(s):
        unicode2latex = [
            (ur'\u2460', ur'{\text{\ding{172}}}'),
            (ur'\u2461', ur'{\text{\ding{173}}}'),
            (ur'\u2462', ur'{\text{\ding{174}}}'),
            (ur'\u2463', ur'{\text{\ding{175}}}'),
            (ur'\u2464', ur'{\text{\ding{176}}}'),
            (ur'\u2465', ur'{\text{\ding{177}}}'),
            (ur'\u2466', ur'{\text{\ding{178}}}'),
            (ur'\u2467', ur'{\text{\ding{179}}}'),
            (ur'\u2468', ur'{\text{\ding{180}}}'),
            (ur'\u2469', ur'{\text{\ding{181}}}'),
            (ur'\u2160', ur'{\text{\(\mathrm{I}\)}}'),
            (ur'\u2161', ur'{\text{\(\mathrm{II}\)}}'),
            (ur'\u2162', ur'{\text{\(\mathrm{III}\)}}'),
            (ur'\u2163', ur'{\text{\(\mathrm{IV}\)}}'),
            (ur'\u2164', ur'{\text{\(\mathrm{V}\)}}'),
            (ur'\u2165', ur'{\text{\(\mathrm{VI}\)}}'),
            (ur'\u2166', ur'{\text{\(\mathrm{VII}\)}}'),
            (ur'\u2167', ur'{\text{\(\mathrm{VIII}\)}}'),
            (ur'\u2168', ur'{\text{\(\mathrm{IX}\)}}'),
            (ur'\u2169', ur'{\text{\(\mathrm{X}\)}}'),
            (ur'\u00a0', ur' '),
            (ur'\overparen', ur'\wideparen'),
            (ur'\lt', ur'<'),
            (ur'\gt', ur'>'),
            (ur'\u007f', ur''),
            (ur'{align}', ur'{matrix}'),
            (ur'{split}', ur'{aligned}'),
            (ur'\uff1d', ur'='),
            (ur'\Omega', ur'\text{$\Omega$}'),
            (ur'\style{font-family:Times New Roman}{g}', ur'\textsl{g}'),
            (ur'_\rm', ur'_\phrm'),
            (ur'^\rm', ur'^\phrm'),
            (ur'[[nn]]', ur'\dd '),
            (ur'\u200b', ur''),
        ]
        for uni, latex in unicode2latex:
            s = s.replace(uni, latex)
        return s

    ori = unicode_2_latex(ori)

    ori = re.sub(img_re4, ur'', ori)
    print ori
    ori = re.sub(img_re3, ur'', ori)
    print ori
    ori = re.sub(ur'(?<!(?:\\|%))%', ur'\%', ori)
    ori = cn_in_mathmode(ori)
    ori = re.sub(
        ur'\\begin\s?{array}[\s\S]*?\\end\s?{array}', array_col_correction, ori)
    ori = re.sub(ur'\[\[un\]\]([\s\S]*?)\[\[/un\]\]',
                 lambda x: u'\\uline{%s}' % x.group(1), ori)
    ori = re.sub(ur'\u005f\u005f+', ur'\\dd ', ori)
    ori = ori.replace(u'\n\n', '\n')
    print ori
    return ori
a = u'1341234513512341\\begin{array}{cc}1&中文2\\\\2&4\\end{array}1231231231b'
print str2latex(a)
