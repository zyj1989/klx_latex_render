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


def str2latex(ori):
    def array_in_mathmode(s):  # by ningshuo
        def _deal(s, math_end):
            stop = s.find(ur'\)')
            print stop
            if stop == -1:
                s = re.sub(ur'\\begin\s?{array}', ur'\[\\begin{array}', s)
                s = re.sub(ur'\\end\s?{array}', ur'\\end{array}\]', s)
            else:
                s = s[
                    :stop] + re.sub(ur'\\begin\s?{array}', ur'\[\\begin{array}', s[stop:])
            return s

        s = re.split(ur'(?<!\\)\\\(', s)
        show_pretty_dict(s)
        for idx, str in enumerate(s, start=0):
            s[idx] = _deal(str, ur'(?<!\\)\\\)')
        s = ur'\('.join(s)
        return s

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
    ori = re.sub(img_re2, ur'[[img]]img[[/img]]', ori)
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
        opt_imgs = re.findall(img_file_re, opt)
        if opt_imgs:
            opt_imgs_cnt += 1
    if opt_imgs_cnt == 4:
        return '\\imgch'
    else:
        return '\\ch'


def get_opt_img(opt, img_width):
    opt = punc_in_img(opt)
    opt_imgs = re.findall(img_file_re, opt)
    if opt_imgs:
        for img_file in opt_imgs:
            if not os.path.isfile('{}{}'.format(img_path, img_file)):
                img_f = open('{}{}'.format(img_path, img_file), 'w')
                img_f.write(urllib2.urlopen(
                    '{}{}'.format(img_url, img_file)).read())
            opt += '\\includegraphics[width={}\\textwidth]{{{}{}}}'.format(
                img_width, img_path, img_file)
    # opt = re.sub(img_re2, '', opt)
    return opt


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
            opt_tex += '{%s}' % opt
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
dbname = 'klx_math'
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
item_ids = ['561609265417d174cb1a3b2f']


def do_items(item_ids, subject):
    tex = template
    dbname = subject
    for item_id in item_ids:
        tex += item_latex_render(ObjectId(item_id))
    tex += u'\\end{document}'
    return tex


item_ids = [
    # '537dcbcbe138230941ea216c',
    '537dcbcbe138230941ea21dd',
    '537dcbcbe138230941ea2225',
    '537dcbcce138230941ea2248',
    '537dcbcde138230941ea2343',
    '537dcbd3e138230941ea2439',
    '537dcbd4e138230941ea24ef',
    '537dcbd7e138230941ea2677',
    '537dcbd7e138230941ea26c4',
    '537dcbd7e138230941ea26c5',
    '537dcbe9e138230941ea28e3',
    '537dcbebe138230941ea29eb',
    '537dcbebe138230941ea2a01',
    # '537dcbfde138230941ea2db0',
    '537dcc05e138230941ea3014',
    '537dcc06e138230941ea30f6',
    # '537dcc07e138230941ea3178',
    # '537dcc07e138230941ea317f',
    '537dcc07e138230941ea31f1',
    '537dcc07e138230941ea31fa',
    '537dcc07e138230941ea325e',
    '537dcc08e138230941ea329f',
    '537dcc08e138230941ea32d7',
    '537dcc0fe138230941ea3442',
    '537dcc10e138230941ea34bd',
    '537dcc10e138230941ea34bf',
    '537dcc10e138230941ea34d3',
    '537dcc10e138230941ea34d4',
    '537dcc11e138230941ea358b',
    '537dcc13e138230941ea35fe',
    '537dcc14e138230941ea3667',
    '537dcc14e138230941ea36fe',
    '537dcc15e138230941ea375f',
    # '537dcc25e138230941ea37e9',
    '537dcc26e138230941ea384f',
    # '537e9fd6e138230941ea4bb9',
    '537ea846e138230941ea4bf1',
    '537ea846e138230941ea4bf9',
    '537f3713e1382317f8c42ab2',
    '537f40afe1382317f8c42b95',
    # '537fe4dce1382317f8c42d44',
    # '537fe4dde1382317f8c42d46',
    '537fe98de1382317f8c42dd5',
    '53801a4ce1382317f8c42e55',
    '5380492de1382317f8c42f88',
    '53c4900fe1382317a62dc540',
    '53c4a4ede13823179bcd0377',
    '53c4a505e1382317a62dc5cc',
    '53c4a517e13823179bcd0382',
    '53c4d0ebe1382317a62dc6a7',
    '53c4d719e13823179bcd0502',
    '53c4e71ee1382317a62dc7e5',
    '53c5d968e1382317a62dc8d1',
    '53c5db2be1382317a62dc8f3',
    '53c5e796e1382317a62dca4c',
    '53c5e81de13823179bcd07c9',
    '53c5ec0be13823179bcd0876',
    '53c62f3fe13823179bcd09ed',
    '53c64c10e13823179bcd0b0b',
    '543f74af0045fe48f83733d2',
    '548a62400045fe78c17c32da',
    '56a1ddb75417d110379eea70',
    '56a1ddc65417d1102e06eef6',
    '56af0b205417d10805017586',
    '56c46e0f5417d124e44b1ada',
    '56c68a5b5417d10c6d3c6884',
    '56c68a5b5417d10c6d3c6887',
    '56c6ce355417d10805018999',
    '56cafc415417d12215e67dc2',
    '56d3ff785417d10edf4e3d75',
    '56d4e1635417d10c6d3c6cb3',
    '56d513695417d108050193f1',
    '56d5593b5417d10c6d3c6e6a',
    '56dd4a8e5417d15e378d717b',
    '56e8f2a35417d156e0348cd2',
    '56e915725417d156e0348ff5',
    '56ecee075417d1131ec9053c',
    '56ecf70d5417d1131d4bf430',
    '56ee67c35417d1131d4bf6d0',
    '56eea6ca5417d1131d4bf74a',
    '56eeacca5417d1131ec908bb',
    '56ef43075417d1131d4bf834',
    '56ef56ee5417d156e034a037',
    '56ef8be55417d156e034a2ab',
    '56ef8be55417d156e034a2ac',
    '56ef8be55417d156e034a2ad',
    '56efcbd55417d1131ec90dcc',
    '56f101ea5417d1131ec91177',
    '56f105375417d1131d4c007e',
    '56f1e3e25417d15b3ead70cc',
    '56f4cdf35417d140a1f1bc22',
    '56f5331c5417d175d1750b41',
    '56f77a465417d175d17510b6',
    '56f78fd55417d175d07511e4',
    '56f88dcb5417d15b16270a0b',
    '56f8a1e55417d175d0751597',
    '56f9239b5417d175d1751922',
    '56f9267b5417d175d1751941',
    '56fa0e2c5417d175d1751c00',
    '56fa23f75417d175d1751ccb',
    '56fa73eb5417d162b50508f4',
    '56fb48055417d162b5050c10',
    '56fb4bc65417d162b60db33e',
    '56fb4c5f5417d162b5050c9e',
    '56fb4ef05417d162b60db384',
    '56fb4f575417d162b60db38f',
    '56fb91b75417d162b5050fd8',
    '56fba1975417d162b505108d',
    '56fcb61d5417d162b50515e2',
    '56fd091f5417d13b21c21d0c',
    '56fe45ae5417d176046741bf',
    '56fe68525417d1760593e4db',
    '56fe6cb35417d17604674270',
    '56fe9b8f5417d1760593e6b7',
    '56ff9d6e5417d17604674662',
    '56ffd1115417d17604674714',
    '5700c7225417d1760593ecf8',
    '5703a64c5417d1760593fb02',
    '57051cda5417d17604676057',
    '570630d95417d17604676583',
    '570773895417d17604676b02',
    '570774845417d17605940d42',
    '5708a3fd5417d1760594127f',
    '570b17145417d134eadf1cc0',
    '570cacdf5417d11e10c5df53',
    '570cc7eb5417d11e11e7f999',
    '570ddfdd5417d14950dd7e3a',
    '570f4f735417d11991eff88e',
    '570f9f5cdef29755473b3ea1',
    '570fa624def29755473b3ed7',
    '570fae2fdef297556aaa3379',
    '5710703bdef29755473b417a',
    '571107ecdef2970a16651b2e',
    '57110a62def2970a16651b63',
    '57110cf0def2970a16651b7c',
    '57110e61def2970a155efa88',
    '5711a16ddef2970a16651cb0',
    '5711f24fdef2970a16651f4d',
    '57120034def2970a16651f9e',
    '57120fbedef2970a1665201f',
    '57125f8fdef2970a155f0353',
    '57132102def2970a155f066a',
    '571330dbdef2970a155f0767',
    '571433d6def2970a16652ba8',
    '57159b3fdef2977c21a5ac5a',
    '5715fafcdef2977c21a5b0a5',
    '57162537def2977c1b89a108',
    '57162754def2977c1b89a11e',
    '5716275bdef2977c1b89a122',
    '57170a67def2977c21a5b7a7',
    '5717973fdef2977c1b89aa34',
    '57188c8bdef2977c1b89af2b',
    '5719c98edef2976dcab38834',
    '571a1d83def2970ec5836d7c',
    '571a2fd5def2970ec5836dfb',
    '571ab9b4def2970ec5836f09',
    '571b32abdef2970e65c96c80',
    '571b5370def2970e65c96d44',
    '571b7106def2970ec583738e',
    '571b7684def2970e65c96e6d',
    '571d764cdef2970e65c9742e',
    '571db028def2970e65c9758b',
    '571db16fdef2970e65c975b1',
    '571de74edef2970ec5837d58',
    '571e112ddef2970ec5837ea0',
    '571f57d6def2970ec583864d',
    '571f7abedef2970e65c981db',
    '57203056def2970e65c983a3',
    '5720638adef2970e65c9850a',
    '57206678def2970ec5838b0e',
    '5720686adef2970ec5838b25',
    '57207eacdef2970ec5838be8',
    '5720cdd2def2970ec5838dc5',
]
subject = 'klx_math'
path = paper_path
f = open('{}{}.tex'.format(path, '111111111'), 'w')
f.write(do_items(item_ids, subject))
f.close
