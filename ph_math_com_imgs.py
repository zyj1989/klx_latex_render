#!/usr/bin/env python
# encoding:utf-8
'''
item render with minipage 
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
    if len(opts) == 3:
        result = '\\trech'
    elif len(opts) == 5:
        result = '\\fivch'
    elif len(opts) == 4:
        for opt in opts:
            opt = punc_in_img(opt)
            opt_imgs = re.findall(img_file_re, opt)
            if opt_imgs:
                opt_imgs_cnt += 1
            opt = re.sub(img_re3, '', opt)
        if opt_imgs_cnt == 4:
            result = '\\imgch'
        else:
            result = '\\ch'
    else:
        result = ''
    return result


def get_opt_img(opt, img_width):
    opt = punc_in_img(opt)
    opt_imgs = re.findall(img_file_re, opt)
    opt_img = ''
    if opt_imgs:
        for img_file in opt_imgs:
            file_path_name = os.path.join(img_path, img_file)
            if not os.path.isfile(file_path_name):
                urllib.urlretrieve('{}{}'.format(
                    img_url, img_file), file_path_name)
                print file_path_name
            im = Image.open(file_path_name)
            arg = 'width'
            if im.size[0] < im.size[1]:
                # adjust the longer one between width end height
                arg = 'height'
            opt_img = '\\includegraphics[{}={}\\optwidth]{{{}}}'.format(
                arg, img_width, os.path.join(img_path, img_file))
    opt = re.sub(img_re3, '', opt)
    opt = re.sub(ur'\n', '', opt)
    return [opt, opt_img]


def deal_desc_img(desc):
    result = {
        'text': '',
        'imgs': '',
    }
    desc = punc_in_img(desc)
    desc_imgs = re.findall(img_re2, desc)
    scale = 0.7
    scale = 0.5
    img_inpar_tex = ''
    img_display_tex = ''
    for desc_img in desc_imgs:
        img_file = re.findall(img_file_re, desc_img)[0]
        file_path_name = os.path.join(img_path, img_file)
        if not os.path.isfile(file_path_name):
            urllib.urlretrieve('{}{}'.format(
                img_url, img_file), file_path_name)
            print img_file
        if 'src' in desc_img:
            img_json = json.loads(desc_img[7:-8])
        else:
            img_json = ''
        im = Image.open(file_path_name)
        size = []
        print img_json
        if 'width' in img_json:
            size_w = int(img_json['width']) * scale
            size.append('width={}pt'.format(str(size_w)))
        else:
            size_w = im.size[0]

        if 'height' in img_json:
            size_h = int(img_json['height']) * scale
            size.append('height={}pt'.format(str(size_h)))
        else:
            size_h = im.size[1]

        size = ','.join(size)
        print size
        if size_w > 180 and size_w < 501:
            img_display_tex += u'\\includegraphics[{}]{{{}}}'.format(
                size, file_path_name)
        elif size_w > 500:
            img_display_tex += u'\\includegraphics[width=\\optwidth]{{{}}}'.format(
                file_path_name)
        else:
            img_inpar_tex += u'\\includegraphics[{}]{{{}}}'.format(
                size, file_path_name)
    desc_tex = re.sub(img_re3, ur'', desc)
    if img_display_tex != '':
        desc_tex += u'\\newline %s' % img_display_tex
    result['imgs'] = img_inpar_tex
    result['text'] = str2latex(desc_tex)
    return result


def deal_with_qs(qs, item_type):
    if item_type not in [1001, 1002, 2001, 2002]:
        #     desc_tex = deal_desc_img(qs['desc'])
        #     opts = qs['opts']
        #     opt_tex = get_opts_head(opts)
        #     for opt in opts:
        #         opt = get_opt_img(opt, 0.222)
        #         opt_tex += '{%s}{%s}' % (opt[0], opt[1])
        #     qs_tex += str2latex(opt_tex)
        # else:
        desc_tex = qs['desc']
        qs_tex = str2latex(desc_tex)
        qs_tex += u'\n'
        opts = qs['opts']
        opt_tex = get_opts_head(opts)
        for opt in opts:
            opt = get_opt_img(opt, 0.222)
            opt_tex += '{%s}{%s}' % (opt[0], opt[1])
        qs_tex += str2latex(opt_tex)
    return qs_tex


def item_latex_render(item_id):
    item = db.items.find_one({'_id': item_id})
    qs_tex = u''
    if not item:
        print item_id
        return '%%%%%%%%%%%%%%%%'
    tex = '\r%% {} {}\r'.format(
        item_id, item['data']['type'])
    if item['data']['type'] in [1001, 2001, 1002, 2002]:
        tex += '\\begin{questions}'
        varwidth = width_map[item['data']['type']]
        qs = item['data']['qs'][0]
        desc = deal_desc_img(qs['desc'])
        opts = qs['opts']
        opt_tex = get_opts_head(opts)
        for opt in opts:
            opt = get_opt_img(opt, 0.222)
            opt_tex += '{%s}{%s}' % (opt[0], opt[1])
        opt_tex = str2latex(opt_tex)
        tex += u'\\klxitem{%s}{%s}{%s}{%s}' % (
            desc['text'], opt_tex, desc['imgs'], varwidth)

    elif item['data']['type'] in [1003, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 4003, 4004, 3003, 3004]:
        tex += '\\begin{{questions}}\n\\begin{{varwidth}}'
        tex += '{{{}}}'.format(width_map[1003])
        if len(item['data']['stem']) == 0:
            if len(item['data']['qs']) == 1:
                print item['_id']
                qs = item['data']['qs']
                tex += deal_with_qs(qs, item['data']['type'])
            else:
                tex += u'\\begin{subquestions}\n'
                for qs in item['data']['qs']:
                    qss_tex = u''
                    if len(qs['desc']) != 0:
                        qs_tex += u'\wqq '
                        qs_tex += deal_with_qs(qs, item['data']['type'])
                    if 'qs' in qs:
                        qss_tex += u'\\begin{subsubquestions}\n'
                        for qss in qs['qs']:
                            qss_tex += u'\wqqq '
                            qss_tex += deal_with_qs(qss, item['data']['type'])
                        qss_tex += u'\\end{subsubquestions}\n'
                    qs_tex += qss_tex
                tex += qs_tex
                tex += u'\\end{subquestions}\n'
        else:
            tex += str2latex(item['data']['stem'])
            if len(item['data']['qs'][0]['desc']) != 0:
                tex += u'\\vspace{-1em}\\begin{subquestions}\n'
                for qs in item['data']['qs']:
                    qss_tex = u''
                    if len(qs['desc']) != 0:
                        qs_tex += u'\wqq '
                        qs_tex += deal_with_qs(qs, item['data']['type'])
                    if 'qs' in qs:
                        qss_tex += u'\\begin{subsubquestions}\n'
                        for qss in qs['qs']:
                            qss_tex += u'\wqqq '
                            qss_tex += deal_with_qs(qss, item['data']['type'])
                        qss_tex += u'\\end{subsubquestions}\n'
                    qs_tex += qss_tex
                tex += qs_tex
                tex += u'\\end{subquestions}\n'
        tex += u'\\end{varwidth}\n'
    tex += u'\\end{questions}'
    if item['data']['type'] in [1001, 2001, 3001, 4001]:
        tex = tex.replace(ur'\dd ', ur'\dq ')
        # tex = re.sub(ur'\\begin{question}\s?\\\\', ur'\\begin{question}', tex)
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


def get_items(item_ids, subject):
    tex = template
    dbname = subject
    for item_id in item_ids:
        print item_id
        tex += item_latex_render(ObjectId(item_id))
        # tex += '\\\\'  # used for multi-items
    tex += u'\n\\end{document}'
    return tex


def do_multi_items_test(skip, limit):
    item_ids_cursor = db.items.find({'deleted': False,
                                     'data.type': 1001
                                     }, {
        '_id': 1}).skip(skip).limit(limit)
    item_ids = []
    for item in item_ids_cursor:
        item_ids.append(item['_id'])
    tex = get_items(item_ids, subject)
    f = open(os.path.join(paper_path, '{}.tex'.format(skip)), 'w')
    f.write(tex)
    f.close()
    print skip


def do_certain_items(item_ids, subject):
    tex = get_items(item_ids, subject)
    f = open(os.path.join(paper_path, 'test.tex'), 'w')
    f.write(tex)

"""
=== Setting =============================================================
"""
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
dbname = 'klx_ph'
db = client[dbname]


subject = 'klx_ph'
paper_path = '../papers'
item_path = '../items'
# img_path = '../imgs/'
img_path = '/Users/zhangyingjie/var/data/img'
# img_re2 = re.compile(ur'\n\[\[img\]\].*?\[\[/img\]\]')
img_re2 = re.compile(ur'\[\[img\]\].*?\[\[/img\]\]')  # used for desc imgs
# used for delete imgs urls
img_re3 = re.compile(ur'\n?\s?\u200b?\[\[img\]\].*?\[\[/img\]\]')
img_file_re = re.compile(ur'\w+\.(?:png|jpg|gif|bmp|jpeg)')
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
item_ids = [
    ObjectId("55dc2c0e5417d1698e554c3f"),
    ObjectId("55dc2c575417d1698e554c43"),
    ObjectId("55dfceca5417d14d2d0866ff"),
    ObjectId("55dfd3315417d14e27e0f691"),
    ObjectId("55dc2c0e5417d1698e554c3f"),
    ObjectId("55dc2c575417d1698e554c43"),
    ObjectId("55dfceca5417d14d2d0866ff"),
    ObjectId("55dfd3315417d14e27e0f691"),
    '55f69bf35417d174cc827da4',
    ObjectId("55dc2c0e5417d1698e554c3f"),
    ObjectId("55dc2c575417d1698e554c43"),
    ObjectId("55dfceca5417d14d2d0866ff"),
    ObjectId("55dfd3315417d14e27e0f691")
]
item_ids = [  # physics
    '55ebde4d5417d17be13a4c06',
    '55ebde4d5417d17be13a4c08',
    '55ee4f735417d17be0d12783',
    '55eea5445417d17be13a4ced',
    '55ebde235417d17be0d126f7',
    '55ebde915417d17be13a4c14',
]
# #item_ids = [  # math
#     '54b88dda0045fe10ab5e4608',
#     '54be1fc00045fe3e0e53111e',
# ]
# do_multi_items_test(34230, 500)
do_certain_items(item_ids, subject)
