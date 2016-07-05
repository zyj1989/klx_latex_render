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
import cStringIO
from PIL import Image
from bson.objectid import ObjectId
from pymongo import MongoClient
from func import show_pretty_dict

template = ur'''% !TEX encoding=utf8
% !TEX program=xelatex
\documentclass{klx}
\begin{document}
'''


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
            (ur'\u2160', ur'\mathrm{I}'),
            (ur'\u2161', ur'\mathrm{II}'),
            (ur'\u2162', ur'\mathrm{III}'),
            (ur'\u2163', ur'\mathrm{IV}'),
            (ur'\u2164', ur'\mathrm{V}'),
            (ur'\u2165', ur'\mathrm{VI}'),
            (ur'\u2166', ur'\mathrm{VII}'),
            (ur'\u2167', ur'\mathrm{VIII}'),
            (ur'\u2168', ur'\mathrm{IX}'),
            (ur'\u2169', ur'\mathrm{X}'),
            (ur'\overparen', ur'\wideparen'),
            (ur'\lt', ur'<'),
            (ur'\gt', ur'>'),
            (ur'\u007f', ur''),
            (ur'{align}', ur'{matrix}'),
            (ur'{split}', ur'{aligned}'),
            (ur'\uff1d', ur'='),
            (ur'\Omega', ur'\text{$\Omega$}'),
            (ur'\style{font-family:Times New Roman}{g}', ur'\textsl{g}')
        ]
        for uni, latex in unicode2latex:
            s = s.replace(uni, latex)
        return s
    # print ori
    ori = unicode_2_latex(ori)
    # ori = re.sub(img_re2, ur'[[img]]img[[/img]]', ori)
    ori = re.sub(img_re3, ur'', ori)
    ori = re.sub(ur'(?<!(?=\\|%))%', '\%', ori)
    ori = cn_in_mathmode(ori)
    ori = re.sub(
        ur'\\begin\s?{array}[\s\S]*?\\end\s?{array}', array_col_correction, ori)
    ori = re.sub(ur'\u005f\u005f+', ur'\\dd ', ori)
    ori = ori.replace(u'\n\n', '\n')
    return ori


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


def get_opts_head(opts):
    opt_imgs_cnt = 0
    for opt in opts:
        opt = punc_in_img(opt)
        print opt
        opt_imgs = re.findall(img_file_re, opt)
        if opt_imgs:
            opt_imgs_cnt += 1
        opt = re.sub(img_re3, '', opt)
    if opt_imgs_cnt == 4:
        result = '\\imgch'
    else:
        result = '\\ch'
    return result


def get_opt_img(opt, img_width):
    opt = punc_in_img(opt)
    opt_imgs = re.findall(img_file_re, opt)
    opt_img = ''
    if opt_imgs:
        for img_file in opt_imgs:
            file_path_name = '{}{}'.format(img_path, img_file)
            if not os.path.isfile(file_path_name):
                img_f = open(file_path_name, 'w')
                img_f.write(urllib2.urlopen(
                    '{}{}'.format(img_url, img_file)).read())
            tmp_img = cStringIO.StringIO(open(file_path_name).read())
            im = Image.open(tmp_img)
            print im.size[0], im.size[1]
            arg = 'width'
            if im.size[0] < im.size[1]:
                # adjust the longer one between width end height
                arg = 'height'
            opt_img = '\\includegraphics[{}={}\\textwidth]{{{}{}}}'.format(
                arg, img_width, img_path, img_file)
    opt = re.sub(img_re3, '', opt)
    opt = re.sub(ur'\n', '', opt)
    return [opt, opt_img]


# def get_desc_img(desc):
#     desc_imgs = re.findall(img_file_re, desc)
#     if len(desc_imgs) == 1:
#         tex = ur''


def item_latex_render(item_id):
    tex = '%% {}\n\\begin{{question}}'.format(item_id)
    item = db.items.find_one({'_id': item_id})
    qs_tex = u''
    if not item:
        print item_id
        return '%%%%%%%%%%%%%%%%'
    if item['data']['type'] in [1001, 2001]:
        tex += str2latex(item['data']['qs'][0][
            'desc'].replace('[[nn]]', '\\dq '))
        opts = item['data']['qs'][0]['opts']
        opt_tex = get_opts_head(opts)
        for opt in opts:
            opt = get_opt_img(opt, 0.222)
            opt_tex += '{%s}{%s}' % (opt[0], opt[1])
        tex += str2latex(opt_tex)
    elif item['data']['type'] in [1002, 2002]:
        tex += str2latex(item['data']['qs'][0][
            'desc'].replace('[[nn]]', '\\dd '))
    elif item['data']['type'] in [1003, 2003, 2004, 2005]:
        if len(item['data']['stem']) == 0:
            pass
        else:
            tex += str2latex(item['data']['stem'].replace('[[nn]]', '\\dq '))
        if len(item['data']['qs'][0]['desc']) != 0:
            tex += u'\\begin{subquestions}\n'
            for qs in item['data']['qs']:
                qss_tex = u''
                if len(qs['desc']) != 0:
                    qs_tex += u'\wqq {}\n'.format(str2latex(
                        qs['desc'].replace('[[nn]]', '\\dd ')))
                if 'qs' in qs:
                    qss_tex += u'\\begin{subsubquestions}\n'
                    for qss in qs['qs']:
                        qss_tex += u'\wqqq {}\n'.format(str2latex(
                            qss['desc'].replace('[[nn]]', '\\dd ')))
                    qss_tex += u'\\end{subsubquestions}\n'
                qs_tex += qss_tex
            tex += qs_tex
            tex += u'\\end{subquestions}\n'

    tex += u'\\end{question}\n'
    tex = re.sub(ur'\\begin{question}\s?\\\\', ur'\\begin{question}', tex)
    # tex = tex.replace(ur'\begin{question}\\', ur'\begin{question}')
    # desc = get_opt_img(desc, 0.5)
    # qss = re.sub(img_re2, u'\\ ', qss)
    # desc = str2latex(desc)
    # qss = str2latex(qss)
    # opt_tex = str2latex(opt_tex)
    # item_tex = '\\\\\n'.join(tex_list)
    # # item_tex = u'%{}\n{}\\\\\n{}\\\\\n{}'.format(
    # # item_id, desc, qss, opt_tex)

    # return item_tex
    return tex


def klx_paper_render(paper):

    def _deal_paper_head(paper):
        return '%% {id}\n\\begin{{center}}\n{paper_name}\n\\end{{center}}'.format(id=paper['_id'], paper_name=paper['name'])

    def _deal_part_head(part):
        item_type = itmtyp_2_name[part[0]['type']]
        return u'\\wns {} \\\\*\n'.format(item_type)

    result_tex = template
    result_tex += _deal_paper_head(paper)
    for part in paper['parts']:
        result_tex += _deal_part_head(part)
        for item in part:
            result_tex += item_latex_render(item['item_id'])

    result_tex += '\\end{document}'
    return result_tex
""" 
=== Setting =============================================================
"""
pdf_width = u'\\textwidth'
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
dbname = 'klx_ph'
db = client[dbname]


paper_path = '../papers/'
item_path = '../items/'
img_path = '../imgs/'
img_re2 = re.compile(ur'\n\[\[img\]\].*?\[\[/img\]\]')
img_re3 = re.compile(ur'\[\[img\]\].*?\[\[/img\]\]')
img_file_re = re.compile(ur'\w+\.(?:png|jpg|gif|bmp)')
for path in [paper_path, item_path, img_path]:
    if os.path.exists(path):
        pass
    else:
        os.makedirs(path)

# paper_id = ObjectId('572abb4bbbddbd4d2dbd89dc')
# paper = db.papers.find_one({'_id': paper_id})
# f = open('{path}{name}.tex'.format(path=paper_path, name='11'), 'w')
# f.write(klx_paper_render(paper))
# f.close()
item_ids = ['571b8cbcdef2970fea808648',
            '571c7ed2def2970fea80878f',
            "55de87295417d14e27e0f680",
            "56a350125417d1720aa074f4", ]


def do_items(item_ids, subject):
    tex = template
    dbname = subject
    for item_id in item_ids:
        tex += item_latex_render(ObjectId(item_id))
    tex += u'\\end{document}'
    return tex


subject = 'klx_ph'
path = paper_path
f = open('{}{}.tex'.format(path, '2222'), 'w')
f.write(do_items(item_ids, subject))
f.close
