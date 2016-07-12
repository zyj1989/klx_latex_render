#!/usr/bin/env python
# encoding:utf-8
'''
试卷渲染
'''
import re

import sys
from PIL import Image
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('..')
import json
import os
import urllib
from pymongo import MongoClient

width_map = {
    1001: '125.46652mm',
    1002: '100.894444444mm',
    1003: '161.928mm',
    2001: '125.46652mm',
    2002: '100.894444444mm',
    2003: '161.928mm',
    2004: '100.894444444mm',
    2005: '161.928mm',
    2006: '100.894444444mm',
    2007: '161.928mm',
    2008: '161.928mm',
    2009: '161.928mm',
}

pdf_width = u'125.46652mm'
img_url = 'http://www.kuailexue.com/data/img/'

itmtyp_2_name = {1001: '选择题',
                 1002: '填空题',
                 1003: '解答题',
                 2001: '选择题',
                 2002: '填空题',
                 2003: '解答题',
                 2004: '实验题',
                 2005: '模块选做题',
                 2006: '作图题',
                 2007: '科普阅读题',
                 2008: '简答题',
                 2009: '计算题',
                 2010: '综合应用题',
                 }

client = MongoClient('10.0.0.100', 27017)
dbname = 'klx_math'
db = client[dbname]


subject = 'klx_math'
paper_path = '../papers'
item_path = '../items'
# img_path = '../imgs/'
img_path = '/Users/zhangyingjie/var/data/img'
# img_re2 = re.compile(ur'\n\[\[img\]\].*?\[\[/img\]\]')
img_re2 = re.compile(ur'\[\[img\]\].*?\[\[/img\]\]')  # used for desc imgs
# used for delete imgs urls
img_re3 = re.compile(ur'\n?\s?\u200b?\[\[img\]\].*?\[\[/img\]\]')
img_file_re = re.compile(ur'\w+\.(?:png|jpg|gif|bmp|jpeg)')

desc = u'利用计算器[[img]]{"src":"8253afe639af7dd55c4502177c62de02.png"}[[/img]]求 \( \sin 30^\circ \) 时，依次按键[[img]]{"src":"4b62a164e3086670c8f0269ba9076ecc.png"}[[/img]]则计算器上显示的结果是[[nn]]利用计算器求 \\( \\sin 30^\\circ \\) 时，依次按键[[img]]{\"src\": \"328dd2c165c9191e95070ccf47da7f7b.png\"}[[/img]]则计算器上显示的结果是 \\(\\left(\\qquad\\right)\\)'


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
            s = re.sub(ur'(?<!\\)&', u'\\&', s)
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
            (ur'\u2160', ur'\text{$\mathrm{I}$}'),
            (ur'\u2161', ur'\text{$\mathrm{II}$}'),
            (ur'\u2162', ur'\text{$\mathrm{III}$}'),
            (ur'\u2163', ur'\text{$\mathrm{IV}$}'),
            (ur'\u2164', ur'\text{$\mathrm{V}$}'),
            (ur'\u2165', ur'\text{$\mathrm{VI}$}'),
            (ur'\u2166', ur'\text{$\mathrm{VII}$}'),
            (ur'\u2167', ur'\text{$\mathrm{VIII}$}'),
            (ur'\u2168', ur'\text{$\mathrm{IX}$}'),
            (ur'\u2169', ur'\text{$\mathrm{X}$}'),
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
    ori = re.sub(img_re3, ur'', ori)
    ori = re.sub(ur'(?<!(?:\\|%))%', ur'\%', ori)
    ori = cn_in_mathmode(ori)
    ori = re.sub(
        ur'\\begin\s?{array}[\s\S]*?\\end\s?{array}', array_col_correction, ori)
    ori = re.sub(ur'\u005f\u005f+', ur'\\dd ', ori)
    ori = ori.replace(u'\n\n', '\n')
    return ori


def deal_with_img(s):
    img = s.group(0)
    img = punc_in_img(img)
    scale = 0.7
    scale = 0.5
    img_file = re.findall(img_file_re, img)[0]
    file_path_name = os.path.join(img_path, img_file)
    if not os.path.isfile(file_path_name):
        urllib.urlretrieve('{}{}'.format(
            img_url, img_file), file_path_name)
        print img_file
    if 'src' in img:  # 可能不严谨，咨询过相信
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
    raise_height = 0.5 * size_h - 1.6  # 用来对齐行内图片
    # print size_tex
    if size_w > 365:  # img display zoom
        img_tex = u'\\includegraphics[width=\\optwidth]{{{}}}'.format(
            file_path_name)
    elif size_h < 30:  # img inline
        img_tex = u'[[inline]]\ \\raisebox{{-{}pt}}{{\\includegraphics[{}]{{{}}}}}\ [[/inline]]'.format(
            raise_height, size_tex, file_path_name)
    elif size_w > 200:  # img display real
        img_tex = u'\\includegraphics[{}]{{{}}}'.format(
            size_tex, file_path_name)
    else:  # img inpar
        img_tex = u'[[inpar]]\\includegraphics[{}]{{{}}}[[/inpar]]'.format(
            size_tex, file_path_name)
    return img_tex


def deal_desc_img(desc):
    result = {
        'text': '',
        'imgs': '',
    }
    desc = punc_in_img(desc)
    s = re.sub(img_re2, deal_with_img, desc)
    print s
    print '+++++++'
    img_inpar = re.findall(ur'\[\[inpar\]\](.*?)\[\[/inpar\]\]', s)
    desc_text = re.sub(ur'\[\[inpar\]\](.*?)\[\[/inpar\]\]', u'', s)
    desc_text = re.sub(
        ur'\[\[inline\]\](.*?)\[\[/inline\]\]', lambda x: x.group(1), desc_text)
    print img_inpar
    img_inpar = u''.join(img_inpar)
    result['imgs'] = img_inpar
    result['text'] = str2latex(desc_text)
    return result

print deal_desc_img(desc)['text']
