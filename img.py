#!/usr/bin/env python
# encoding:utf-8
'''
试卷渲染
'''
import re
import time
import sys
import os
import json
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('..')
import copy
import logging
import urllib
import urllib2
import StringIO
from PIL import Image
from bson.objectid import ObjectId
from pymongo import MongoClient
from func import show_pretty_dict
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
    ur'(\[\[img\]\].*?\[\[/img\]\])')
img_re4 = re.compile(ur'\[\[img\]\].*?\[\[/img\]\]\u200b?\s?\n')
img_file_re = re.compile(ur'\w+\.(?:png|jpg|gif|bmp|jpeg|tif)')
img_display_pattern = re.compile(ur'\[\[display\]\](.*?)\[\[/display\]\]')
img_inpar_pattern = re.compile(ur'\[\[inpar\]\](.*?)\[\[/inpar\]\]')
img_inline_pattern = re.compile(ur'\[\[inline\]\](.*?)\[\[/inline\]\]')


def math_opr(s):
    return s


def text_opr(s):
    return s


def inline_img_speci(s):
    img = s.group(1)
    img_info = fetch_img(img)
    img_tex = u'[[inline]]\ \\raisebox{{-{}pt}}{{\\includegraphics[{}]{{{}}}}}\ [[/inline]]'.format(
        img_info['raise_height'], img_info['size_tex'], img_info['img_file'])
    return img_tex


def ninline_img_speci(s):
    img = s.group(1)
    img_info = fetch_img(img)
    if img_info['size_w'] > 365:  # img display zoom
        img_tex = u'[[display]]\\includegraphics[width=\\optwidth]{{{}}}[[/display]]'.format(
            img_info['img_file'])
    elif img_info['size_w'] > 200:  # img display real
        img_tex = u'[[display]]\\includegraphics[{}]{{{}}}[[/display]]'.format(
            img_info['size_tex'], img_info['img_file'])
    else:  # img inpar
        img_tex = u'[[inpar]]\\includegraphics[{}]{{{}}}[[/inpar]]'.format(
            img_info['size_tex'], img_info['img_file'])
    return img_tex


def display_img_speci(s):
    img = s.group(1)
    img_info = fetch_img(img)
    img_tex = u'\\includegraphics[{}]{{{}}}'.format(
        img_info['size_tex'], img_info['img_file'])
    return img_tex


def imgs_opr(s):
    def _line_opr(line):
        s = re.sub(img_re3, u'', line)
        s = re.sub(ur'\s', u'', s)
        non_img_text = len(s)
        imgs_cnt = len(re.findall(img_re3, line))
        if non_img_text != 0:
            line = re.sub(img_re3, inline_img_speci, line)
        elif imgs_cnt == 1:
            line = re.sub(img_re3, ninline_img_speci, line)
        elif imgs_cnt > 1:
            line = re.sub(img_re3, display_img_speci, line)
            line = u'[[display]]' + line + u'[[/display]]'
        return line
    s = re.split('\n', s)
    for idx, line in enumerate(s, start=0):
        s[idx] = _line_opr(line)

    s = u'\n'.join(s)
    return s


def mode_dep_opr(s, math_opr, text_opr):

    def _dealdisplay(s, idx):
        if idx == 0:
            text = s
            text = text_opr(text)
            s = text
        else:
            stop = s.find(ur'\]')
            stopp = stop + 2
            math = s[:stop]
            math = math_opr(math)
            text = s[stopp:]
            text = math_opr(text)
            s = math + ur'\]' + text
        return s

    def _dealinline(s, idx):
        if idx == 0:
            s = re.split(ur'(?<!\\)\\\[', s)
            for idx, str in enumerate(s, start=0):
                s[idx] = _dealdisplay(str, idx)
            s = ur'\['.join(s)
        else:
            stop = s.find(ur'\)')
            math = s[:stop]
            math = math_opr(math)
            stopp = stop + 2
            k = s[stopp:]
            k = re.split(ur'(?<!\\)\\\[', k)
            for idx, str in enumerate(k, start=0):
                k[idx] = _dealdisplay(str, idx)
            k = ur'\['.join(k)
            s = math + ur'\)' + k
        return s

    s = re.split(ur'(?<!\\)\\\(', s)
    for idx, str in enumerate(s, start=0):
        s[idx] = _dealinline(str, idx)
    s = ur'\('.join(s)
    return s


def punc_in_img(s):  # by ningshuo
    def _deal(s):
        stop = s.find(ur'[[/img]]')
        assert stop != -1
        result = re.sub(ur'\uff0e',
                        ur'.', s[:stop])
        result = re.sub(ur'\uff1a',
                        ur':', result)
        result = re.sub(ur'\uff0c',
                        ur',', result)
        return result + s[stop:]

    s = re.split(ur'\[\[img\]\]', s)
    for idx, str in enumerate(s[1:], start=1):
        s[idx] = _deal(str)

    s = ur'[[img]]'.join(s)
    return s


def str2latex(ori):
    def array_mathmode_cor(s):
        def text_opr(s):
            s = re.sub(
                ur'\\begin\s?{array}[\s\S]*?\\end\s?{array}', lambda x: ur'\[%s\]' % x.group(), s)
            return s
        s = mode_dep_opr(s, math_opr, text_opr)
        return s

    def cn_in_mathmode(s):  # by ningshuo

        def math_opr(s):
            s = re.sub(ur'[\u4e00-\u9fa5,\u3001]+',
                       lambda x: ur'\text{%s}' % x.group(), s)
            return s

        def text_opr(s):
            # latex_remaining_char = ['$', '%', '&', '#', '^', '_', ]
            s = re.sub(ur'(?<!\\)\$', u'\\$', s)
            s = re.sub(ur'(?<!\\)%', u'\\%', s)
            s = re.sub(ur'(?<!\\)&', u'\\&', s)
            s = re.sub(ur'(?<!\\)#', u'\\#', s)
            s = re.sub(ur'(?<!\\)\^', u'\\^', s)
            s = re.sub(ur'(?<!\\)_', u'\\_', s)
            print 's:'
            show_pretty_dict(s)
            print ';'
            s = imgs_opr(s)
            s = s.replace(u'\n', u'\\par ')
            return s

        s = mode_dep_opr(s, math_opr, text_opr)
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
    ori = punc_in_img(ori)
    ori = array_mathmode_cor(ori)
    ori = cn_in_mathmode(ori)
    # ori = re.sub(img_re3, deal_with_img, ori)
    ori = re.sub(ur'(?<!(?:\\|%))%', ur'\%', ori)
    ori = re.sub(
        ur'\\begin\s?{array}[\s\S]*?\\end\s?{array}', array_col_correction, ori)
    ori = re.sub(ur'\[\[un\]\]([\s\S]*?)\[\[/un\]\]',
                 lambda x: u'\\uline{%s}' % x.group(1), ori)
    ori = re.sub(ur'\u005f\u005f+', ur'\\dd ', ori)
    ori = ori.replace(u'\n\n', '\n')
    ori = re.sub(ur'\s*?}', ur'}', ori)
    # print ori
    return ori


def fetch_img(img):  # download imgs and get size
    scale = 0.6
    img_file = re.findall(img_file_re, img)[0]
    file_path_name = os.path.join(img_path, img_file)
    if not os.path.isfile(file_path_name):
        urllib.urlretrieve('{}{}'.format(
            img_url, img_file), file_path_name)
        # print img_file
    if 'src' in img:
        img_json = json.loads(img[7:-8])
    else:
        img_json = ''
    im = Image.open(file_path_name)
    size = []

    if 'height' not in img_json:
        if 'width' not in img_json:
            size_w = im.size[0] * scale
            size_h = im.size[1] * scale
        else:
            size_w = int(img_json['width']) * scale
            mag = size_w / im.size[0]
            size_h = im.size[1] * mag
    else:
        if 'width' not in img_json:
            size_h = int(img_json['height']) * scale
            mag = size_h / im.size[1]
            size_w = im.size[0] * mag
        else:
            size_w = int(img_json['width']) * scale
            size_h = int(img_json['height']) * scale
    size.append('width=%spt' % size_w)
    size.append('height=%spt' % size_h)
    size_tex = ','.join(size)
    raise_height = 0.5 * size_h - 3.3  #
    result = {
        'size_h': size_h,
        'size_w': size_w,
        'img_file': img_file,
        'raise_height': raise_height,
        'size_tex': size_tex
    }
    return result


def trd_img_speci(img_info):  # add some specification arround imgs
    if img_info['size_w'] > 365:  # img display zoom
        img_tex = u'[[display]]\\includegraphics[width=\\optwidth]{{{}}}[[/display]]'.format(
            img_info['img_file'])
    elif img_info['size_h'] < 25:  # img inline
        img_tex = u'[[inline]]\ \\raisebox{{-{}pt}}{{\\includegraphics[{}]{{{}}}}}\ [[/inline]]'.format(
            img_info['raise_height'], img_info['size_tex'], img_info['img_file'])
    elif img_info['size_w'] > 200:  # img display real
        img_tex = u'[[display]]\\includegraphics[{}]{{{}}}[[/display]]'.format(
            img_info['size_tex'], img_info['img_file'])
    else:  # img inpar
        img_tex = u'[[inpar]]\\includegraphics[{}]{{{}}}[[/inpar]]'.format(
            img_info['size_tex'], img_info['img_file'])
    return img_tex


def deal_with_img(s):  # 完成图片下载、大小读取、缩放、引用类型条件
    img = s.group(1)
    img_info = fetch_img(img)
    img_tex = trd_img_speci(img_info)
    return img_tex

a = u'''表示一个算法的起始和结束，程序框是[[img]]{\"src\": \"3cbf48e989bbb2840a8fcffd4dffead.png\", \"width\": \"50\"}[[/img]]213212312
[[img]]{\"src\": \"f3cbf48e989bbb2840a8fcffd4dffead.png\", \"width\": \"50\"}[[/img]][[img]]{\"src\": \"f3cbf48e989bbb2840a8fcffd4dffead.png\", \"width\": \"50\"}[[/img]]
[[img]]{\"src\": \"f3cbf48e989bbb2840a8fcffd4dffead.png\", \"width\": \"50\"}[[/img]]'''

a = u'利用计算\(\ce{1231 + }\)器求 \\( \\sin 30^\\circ \\) 时，依次按键\n[[img]]{\"src\": \"328dd2c165c9191e95070ccf47da7f7b.png\"}[[/img]][[img]]{\"src\": \"328dd2c165c9191e95070ccf47da7f7b.png\"}[[/img]][[img]]{\"src\": \"328dd2c165c9191e95070ccf47da7f7b.png\"}[[/img]]\n则计算器上显示的结果是 \\(\\left(\\qquad\\right)\\)．'

show_pretty_dict(str2latex(a))
