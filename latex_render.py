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
        def _deal(s, math_end):
            stop = s.find(math_end)
            if stop == -1:
                s = s
            else:
                # s[stop:] = s[stop:].replace(ur'&', ur'\\&')
                s = re.sub(ur'[\u4e00-\u9fa5]+',
                           lambda x: ur'\text{%s}' % x.group(), s[:stop]) + s[stop:]
            return s

        math_mode_delimiter = [
            (ur'\(', ur'\)'),
            (ur'\[', ur'\]'),
        ]
        for math_begin, math_end in math_mode_delimiter:
            s = re.split(ur'(?<!\\)\\%s' % math_begin, s)
            for idx, str in enumerate(s, start=0):
                s[idx] = _deal(str, math_end)
            s = math_begin.join(s)
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
    ori = unicode_2_latex(ori)
    ori = re.sub(ur'(?<!(?=\\|%))%', '\%', ori)
    ori = cn_in_mathmode(ori)
    ori = re.sub(
        ur'\\begin\s?{array}[\s\S]*?\\end\s?{array}', array_col_correction, ori)
    ori = re.sub(ur'\u005f\u005f+', ur'\\dd ', ori)
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


def get_img(opt, img_width):
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
    opt = re.sub(img_re2, '', opt)
    return opt


def item_latex_render(item_id):
    tex_list = ['\n%%{}'.format(item_id)]
    item = db.items.find_one({'_id': item_id})
    qss = ''
    if item['data']['type'] in [1001, 2001]:
        tex_list.append(item['data']['qs'][0][
                        'desc'].replace('[[nn]]', '\\dq '))
        opts = item['data']['qs'][0]['opts']
        opt_tex = get_opts_head(opts)
        for opt in opts:
            opt = get_img(opt, 0.222)
            opt_tex += '{%s}' % opt
        tex_list.append(opt_tex)
    elif item['data']['type'] in [1002, 2002]:
        tex_list.append(item['data']['qs'][0][
                        'desc'].replace('[[nn]]', '\\dd '))
    elif item['data']['type'] in [1003, 2003, 2004, 2005]:
        if len(item['data']['stem']) == 0:
            pass
        else:
            tex_list.append(item['data']['stem'].replace('[[nn]]', '\\dq '))
        for qs in item['data']['qs']:
            if len(qs['desc']) != 0:
                qs = u'\\begin{subquestion} %s \\end{subquestion}\n ' % qs[
                    'desc']
                qs = qs.replace('[[nn]]', '\\dd ')
                qss += qs
            tex_list.append(qss)
        # desc = get_img(desc, 0.5)
        # qss = re.sub(img_re2, u'\\ ', qss)
        # desc = str2latex(desc)
        # qss = str2latex(qss)
        # opt_tex = str2latex(opt_tex)
    item_tex = '\\\\\n'.join(tex_list)
    # item_tex = u'%{}\n{}\\\\\n{}\\\\\n{}'.format(
    # item_id, desc, qss, opt_tex)

    item_tex = re.sub(img_re2, u'', item_tex)
    item_tex = str2latex(item_tex)
    return item_tex


def klx_paper_render(paper):

    def _deal_paper_head(paper):
        return '% {id}\n\\begin{{center}}\n{paper_name}\n\\end{{center}}'.format(id=paper['_id'], paper_name=paper['name'])

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
img_re2 = re.compile(ur'\[\[img\]\].*?\[\[/img\]\]')
img_file_re = re.compile(ur'\w+\.(?:png|jpg|gif|bmp)')
for path in [paper_path, item_path, img_path]:
    if os.path.exists(path):
        pass
    else:
        os.makedirs(path)
# paper_id = ObjectId('576ceae852f60278070777a8')
# paper = db.papers.find_one({'_id': paper_id})
# f = open('{path}{name}.tex'.format(path=paper_path, name=paper['name']), 'w')
# f.write(klx_paper_render(paper))
# f.close()
# item_ids = ['53579ec2e13823200113756f',
#             '5357a552e138232001137696',
#             '5357d19ee138232001137d02',
#             '5357d216e138232001137d13',
#             '5357d28ee138232001137d1c',
#             '5357dae0e138232001137e42',
#             '53587932e1382320011380a8',
#             '53587ad6e1382320011380c2',
#             '53588418e138232001138119',
#             '535886e8e13823200113817a',
#             '53588b02e1382320011381b3',
#             '53588b5ce1382320011381d9',
#             '5358920ee1382357d4b0b6da',
#             '5358920ee1382357d4b0b6e4',
#             '5358933ae1382357d4b0b704',
#             '5358933ae1382357d4b0b707',
#             '53589c5ee1382357d4b0b78c',
#             '53589ef2e1382357d4b0b7cd',
#             '5358d02ae1382357d4b0b821',
#             '5358d138e1382357d4b0b82d',
#             '5358de3ae1382357d4b0b8b7',
#             '5358e0cee1382357d4b0b8c2',
#             '5358e2cce1382357d4b0b8ce',
#             '5358efece1382357d4b0b979',
#             '5358f8b6e1382357d4b0ba14',
#             '5358f8c0e1382357d4b0ba17',
#             '5358f8c0e1382357d4b0ba1a',
#             '5358f9e2e1382357d4b0ba79',
#             '5358fd2ae1382357d4b0bb99',
#             '53590324e1382357d4b0bc6a',
#             '5359036ae1382357d4b0bc8d',
#             '53590414e1382357d4b0bcb6',
#             '5359073ee1382357d4b0bd83',
#             '535909d2e1382357d4b0be3b',
#             '53592052e1382357d4b0c066',
#             '5359ceeee1382357d4b0c0f4',
#             '5359d056e1382357d4b0c0fd',
#             '535a36c2e1382357d4b0cc06',
#             '535a57b0e1382357d4b0cdd1',
#             '535a6548e1382357d4b0ce02',
#             '535b4030e1382357d4b0cef4',
#             '535b6dd0e1382357d4b0cfc6',
#             '535b88d8e1382357d4b0cfd1',
#             '535e14c2e1382357d4b0d0dc',
#             '535e1846e1382357d4b0d110',
#             '535e1adae1382357d4b0d1be',
#             '535e1adae1382357d4b0d1c0',
#             '535e1cbae1382357d4b0d1fe',
#             '535e1d6ee1382357d4b0d22f',
#             '535e1e7ce1382357d4b0d24a',
#             '535e3cb8e1382357d4b0d312',
#             '535e65bce1382357d4b0d487',
#             '535ef4d2e1382357d4b0d641',
#             '535ef63ae1382357d4b0d68c',
#             '535efbdae1382357d4b0d725',
#             '535efe6ee1382357d4b0d78f',
#             '5361a4f2e1382357d4b0e39b',
#             '5365f0e5e13823572dea204a',
#             '536b0518e13823613f005e73',
#             '536b0a22e13823613f005ec0',
#             '536b5010e138235d32c504fd',
#             '536b5b8ce138235d32c5061b',
#             '536b5b8ce138235d32c50627',
#             '536b5c04e138235d32c50633',
#             '536b5d8ae138235d32c5067e',
#             '536b5fc4e138235d32c506fa',
#             '536b60b4e138235d32c5073c',
#             '536b614ae138235d32c50751',
#             '536b6186e138235d32c5076d',
#             '536b61c2e138235d32c50780',
#             '5370c076e13823248c141e4f',
#             '5371c85fe13823248c142ad4',
#             '5372cbfee138237bbb03be12',
#             '5372d6e4e138237bbb03bfc6',
#             '5372d86ae138237bbb03c01b',
#             '5372d8e2e138237bbb03c068',
#             '5372d8e2e138237bbb03c070',
#             '5372d8e2e138237bbb03c073',
#             '5372d91ee138237bbb03c0b4',
#             '5372d93ce138237bbb03c0c3',
#             '5372d93ce138237bbb03c0c4',
#             '5372d978e138237bbb03c110',
#             '5372db1ce138237bbb03c195',
#             '5372db1ce138237bbb03c198',
#             '5372dc2ae138237bbb03c264',
#             '5372dc2ae138237bbb03c26a',
#             '5372dc2ae138237bbb03c277',
#             '5372dd92e138237bbb03c349',
#             '5372e080e138237bbb03c587',
#             '537723d7e138231f9fcccd0e',
#             '537820bbe138231f9fccd4f2',
#             '537dcaf6e138230941e9ed92',
#             '537dcaf7e138230941e9ee8d',
#             '537dcafae138230941e9effb',
#             '537dcb15e138230941e9f16c',
#             '537dcbade138230941ea18aa',
#             '537dcbade138230941ea18d8',
#             '537dcbade138230941ea1906',
#             '537dcbaee138230941ea1942',
#             '537dcbaee138230941ea1943',
#             '537dcbaee138230941ea19b9',
#             '537dcbafe138230941ea1a2b',
#             '537dcbafe138230941ea1a34',
#             '537dcbafe138230941ea1a67',
#             '537dcbafe138230941ea1a70',
#             '537dcbafe138230941ea1a72',
#             '537dcbb0e138230941ea1b37',
#             '537dcbb0e138230941ea1b40',
#             '537dcbb0e138230941ea1b43',
#             '537dcbb0e138230941ea1b55',
#             '537dcbb0e138230941ea1b5c',
#             '537dcbb0e138230941ea1b65',
#             '537dcbb0e138230941ea1bd9',
#             '537dcbb0e138230941ea1bdb',
#             '537dcbb0e138230941ea1bf5',
#             '537dcbbee138230941ea1c13',
#             '537dcbbfe138230941ea1c80',
#             '537dcbc0e138230941ea1d76',
#             '537dcbc2e138230941ea1efd',
#             '537dcbc3e138230941ea1f9f',
#             '537dcbc3e138230941ea1ff2',
#             '537dcc05e138230941ea301e',
#             '537dcc28e138230941ea3a3d',
#             '537dcc43e138230941ea417c',
#             '537dcc43e138230941ea41d0',
#             '537dcc44e138230941ea4201',
#             '537dcc44e138230941ea422d',
#             '537dcc44e138230941ea424e',
#             '537dcc44e138230941ea425e',
#             '537dcc44e138230941ea42a7',
#             '537dcc45e138230941ea430b',
#             '538046b6e1382317f8c42f2f',
#             '5380bbe7e1382317f8c4349c',
#             '539e567de138236372856cde',
#             '539e5af4e138236379fb226b',
#             '539e905de138236372856d96',
#             '539e906ee138236379fb22de',
#             '539e9079e138236372856d9d',
#             '539ea35be138236379fb232f',
#             '539ea545e138236379fb2340',
#             '539fa71be13823624c26231a',
#             '539fb54fe13823625386b57d',
#             '539fb9d1e13823625386b590',
#             '539fe40ce13823023a4f0987',
#             '539fe42ae138230239ee4f39',
#             '539fe4a4e13823023a4f098b',
#             '539fe7b9e138230239ee4f5e',
#             '539ff941e13823023a4f09ad',
#             '53ab73cde1382368bf449276',
#             '53ab73cde1382368bf449278',
#             '53ab7445e1382368bf449294',
#             '53ab82e6e1382368417628b3',
#             '53ab8cfee13823684fcf6e53',
#             '53ab9227e1382368bf449366',
#             '53ab9227e1382368bf449369',
#             '53abe34ce13823684fcf6f17',
#             '53b0d98de13823684fcf6fd7',
#             '53b0de62e138236841762a8c',
#             '53b108cde138236841762adc',
#             '53b108cde138236841762add',
#             '53b10958e138236841762ae4',
#             '53b12760e138236841762b17',
#             '53b218b5e1382307a21daa6b',
#             '53b255ede1382307a21daacb',
#             '53b2672ce138230817985e67',
#             '53b3c367e13823317fef660e',
#             '53b3c3fee13823318c9a59ce',
#             '53b3ca05e13823317fef6626',
#             '53b4af65e13823318c9a5a2d',
#             '53b4b142e13823317fef6651',
#             '53b4bed7e13823317fef6699',
#             '53b4bf38e13823317fef66a2',
#             '53b4cf9ae13823317fef66d8',
#             '53b4dab3e13823317fef6700',
#             '53ba610be138235b36d59a51',
#             '53bb6adfe138235b4298f40e',
#             '53bb7e6ee138235b36d59c73',
#             '53bc96e0e1382375255149a9',
#             '53bcd3e8e138237525514c9b',
#             '53bdefe3e138237431f8ce12',
#             '53be4b75e1382374b2d0d5fb',
#             '53be4ef9e1382374b2d0d680',
#             '53be4ef9e1382374b2d0d683',
#             '53c73a9fe13823179bcd0c7f',
#             '53c73c19e1382317a62dcd9a',
#             '53ce3103e1382317a62dd5d7',
#             '53d6ff0ee13823179bcd1eb1',
#             '53d894cce1382317a62de04c',
#             '53dafc2ee13823179bcd2166',
#             '53f2f937e13823181b56a89a',
#             '53f30a21e13823179bcd33b7',
#             '53f30de8e13823179bcd33e0',
#             '53f3ec950045fe5a01529ed8',
#             '53f3ed460045fe5a291df2c6',
#             '53f3ef9b0045fe5a291df2e5',
#             '53f4679a0045fe5a966490a0',
#             '53f556aa0045fe5a966490b6',
#             '53f563620045fe5a291df5d7',
#             '53f6e4480045fe5a966490fd',
#             '540676cd0045fe5a0152acd1',
#             '543f71a50045fe487b37f579',
#             '543f71a60045fe487b37f5ce',
#             '543f71a60045fe487b37f5e8',
#             '543f71a60045fe487b37f5ed',
#             '543f71a60045fe487b37f606',
#             '543f71a70045fe487b37f615',
#             '543f71a70045fe487b37f61b',
#             '543f71a90045fe487b37f6e1',
#             '543f71ab0045fe487b37f798',
#             '544076eb0045fe48ff6f7b29',
#             '544076ec0045fe48ff6f7b2a',
#             '547831510045fe78c17c302c',
#             '5487ed200045fe78e2e24562',
#             '5487f5e90045fe78e2e24581',
#             '5488ee2f0045fe78c0ab9dd6',
#             '5488eecd0045fe78c17c3214',
#             '548905120045fe78c0ab9e04',
#             '5489443f0045fe78e2e245f1',
#             '548a5f410045fe78e2e24642',
#             '548a60940045fe78c0ab9e8e',
#             '548a61070045fe78c17c32c0',
#             '548a62e90045fe78c0ab9ea3',
#             '548a67080045fe78c0ab9ea9',
#             '548aba130045fe78e2e2467b',
#             '548abb6b0045fe78c17c332f',
#             '54923d2d0045fe78c17c338a',
#             '549b82a30045fe78e2e2482f',
#             '54afa9590045fe78e2e24a90',
#             '54afa9590045fe78e2e24a97',
#             '54afa9590045fe78e2e24a9b',
#             '54afaf170045fe78e2e24aa9',
#             '54afb0a90045fe10ab5e446d',
#             '54afb0cd0045fe10aaa6b860',
#             '54b3238b0045fe10aaa6b86d',
#             '54b327ec0045fe10aaa6b897',
#             '54b332270045fe78e2e24afb',
#             '54b3374b0045fe10ab5e449b',
#             '54b338050045fe10aaa6b8b3',
#             '54bca9c50045fe7b573f9bc9',
#             '54bcaa9e0045fe7b573f9bd8',
#             '54bcc17f0045fe78e2e24e05',
#             '54bcc17f0045fe78e2e24e0e',
#             '54bf18d80045fe3e0e531513',
#             '54bf1fc20045fe3e0e53151f',
#             '54bf4b580045fe3da7c065a9',
#             '54bf53b30045fe3e0e53163a',
#             '54c08ddd0045fe3e0e531762',
#             '54c08dee0045fe3e0e5317e7',
#             '54c08df10045fe3e0e531800',
#             '54c08df30045fe3e0e53180e',
#             '54c1ae030045fe3e0e5319b6',
#             '54c1f7230045fe3e0e5319ee',
#             '54c1f7240045fe3e0e5319f6',
#             '54d479f70045fe3e0e531deb',
#             '54dd51f10045fe3e0e531e26',
#             '54dd51f10045fe3e0e531e27',
#             '54dd51f10045fe3e0e531e28',
#             '54dd51f10045fe3e0e531e29',
#             '54dd51f60045fe3e0e531e47',
#             '54dd51f90045fe3e0e531e57',
#             '54dd51fb0045fe3e0e531e66',
#             '54dd51fd0045fe3e0e531e75',
#             '54dd51ff0045fe3e0e531e87',
#             '54dd52000045fe3e0e531e8e',
#             '54dd52000045fe3e0e531e8f',
#             '54dd52000045fe3e0e531e91',
#             '54dd52010045fe3e0e531e9c',
#             '54dd52050045fe3e0e531eb5',
#             '54dd52070045fe3e0e531ec8',
#             '54dd52ea0045fe3da7c06d74',
#             '54dd52ea0045fe3da7c06d75',
#             '54dd541b0045fe3da7c06d88',
#             '54dd938e0045fe3e0e531f34',
#             '54dd938e0045fe3e0e531f35',
#             '54dd93910045fe3e0e531f5b',
#             '54dd93930045fe3e0e531f70',
#             '54dd93a30045fe3e0e532003',
#             '54dd947c0045fe3da7c06dab',
#             '54debcc00045fe3e0e532063',
#             '54debcc00045fe3e0e532068',
#             '54debcc00045fe3e0e532069',
#             '54debcc00045fe3e0e53206a',
#             '54debcc20045fe3e0e532076',
#             '54debcc50045fe3e0e53208e',
#             '54debcc90045fe3e0e5320b1',
#             '54debcc90045fe3e0e5320b3',
#             '54debcc90045fe3e0e5320b4',
#             '54debcc90045fe3e0e5320b5',
#             '54debccb0045fe3e0e5320c2',
#             '54debccc0045fe3e0e5320c4',
#             '54debcce0045fe3e0e5320e4',
#             '54debcd10045fe3e0e5320f0',
#             '54debcd70045fe3e0e53211c',
#             '54debcd80045fe3e0e532120',
#             '54ed800c0045fe3e0e53216a',
#             '54ed800e0045fe3e0e53217e',
#             '54ed800f0045fe3e0e532182',
#             '54ed80120045fe3e0e532199',
#             '54ed80190045fe3e0e5321db',
#             '54ed801f0045fe3e0e53220c',
#             '54ed80200045fe3e0e532216',
#             '54ed80220045fe3e0e53222a',
#             '54ed80260045fe3e0e53224c',
#             '54ed80260045fe3e0e53224d',
#             '54ed80280045fe3e0e53225d',
#             '54f130e80045fe3e0e532273',
#             '54f130e80045fe3e0e532278',
#             '54f130eb0045fe3e0e532290',
#             '54f130ed0045fe3e0e5322a3',
#             '54f130ef0045fe3e0e5322b0',
#             '54f130ef0045fe3e0e5322b9',
#             '54f130f40045fe3e0e5322dc',
#             '54f131040045fe3e0e53236d',
#             '54f131040045fe3e0e532370',
#             '54f1329b0045fe3da87d1e6c',
#             '54f1329b0045fe3da87d1e6d',
#             '54f134d60045fe3da87d1e96',
#             '54f134e40045fe3da87d1e9c',
#             '54f134e40045fe3da87d1e9f',
#             '54f134e40045fe3da87d1ea0',
#             '54f16a8f0045fe3e0e53239b',
#             '54f16a900045fe3e0e53239f',
#             '54f16a900045fe3e0e5323a1',
#             '54f16a930045fe3e0e5323ba',
#             '54f16a960045fe3e0e5323d7',
#             '54f16a970045fe3e0e5323e2',
#             '54f16aa30045fe3e0e53244f',
#             '54f16aa70045fe3e0e532477',
#             '54f16aac0045fe3e0e5324aa',
#             '54f16b990045fe3da87d1ea4',
#             '54f16b990045fe3da87d1ea6',
#             '54f16bcb0045fe3da7c06df0',
#             '54f16c3c0045fe3da7c06e04',
#             '54f52f630045fe3e0e5324e5',
#             '54f52f640045fe3e0e5324f1',
#             '54f52f660045fe3e0e53250a',
#             '54f52f690045fe3e0e53252a',
#             '54f52f690045fe3e0e53252f',
#             '54f52f6d0045fe3e0e53254b',
#             '54f52f6f0045fe3e0e53255a',
#             '54f52f790045fe3e0e5325b9',
#             '54f530420045fe3da87d1ea8',
#             '54f6c5300045fe3e0e5325ee',
#             '54f6c53c0045fe3e0e532672',
#             '54f6c53e0045fe3e0e532682',
#             '54f6c95b0045fe3da87d1ed7',
#             '54f7c6a50045fe3e0e532728',
#             '54f7c6aa0045fe3e0e532752',
#             '54f7c6b50045fe3e0e5327bc',
#             '54f7c6c50045fe3e0e53284d',
#             '54f7c6c70045fe3e0e532856',
#             '54f7c6c80045fe3e0e532861',
#             '54f7c77e0045fe3da7c06e57',
#             '54f7c79d0045fe3da87d1ee7',
#             '54f96c6b0045fe3e0e53289c',
#             '54f96c6b0045fe3e0e53289e',
#             '54f96c6b0045fe3e0e53289f',
#             '54f96c6b0045fe3e0e5328a0',
#             '54f96c6b0045fe3e0e5328a1',
#             '54f96c6b0045fe3e0e5328a3',
#             '54f96c6c0045fe3e0e5328aa',
#             '54f96c6c0045fe3e0e5328ae',
#             '54f96c6e0045fe3e0e5328c0',
#             '54f96c6e0045fe3e0e5328c2',
#             '54f96c6e0045fe3e0e5328c3',
#             '54f96cf70045fe3da87d1f08',
#             '54fd43830045fe3e0e53294e',
#             '54fd43830045fe3e0e53294f',
#             '54fd43990045fe3e0e532a19',
#             '54fd44590045fe3da87d1f0d',
#             '54fd44590045fe3da87d1f0e',
#             '54fd46020045fe3da87d1f17',
#             '54ffdf8f0045fe3da87d1f22',
#             '5500fb1c0045fe3e0e532ac3',
#             '5500fb1f0045fe3e0e532ade',
#             '5500fcec0045fe3da7c06e96',
#             '550651f40045fe3e0e532c27',
#             '550651f40045fe3e0e532c28',
#             '550651f40045fe3e0e532c2a',
#             '550651fd0045fe3e0e532c7d',
#             '550651fd0045fe3e0e532c85',
#             '550652070045fe3e0e532ce6',
#             '5506540a0045fe3da7c06ed3',
#             '550655a60045fe3da87d1f75',
#             '550780630045fe3e0e532d3e',
#             '550780640045fe3e0e532d47',
#             '550780670045fe3e0e532d61',
#             '550780680045fe3e0e532d67',
#             '550780690045fe3e0e532d71',
#             '550780690045fe3e0e532d76',
#             '5507806a0045fe3e0e532d7b',
#             '5507806a0045fe3e0e532d7f',
#             '5507806a0045fe3e0e532d84',
#             '5507806d0045fe3e0e532d9d',
#             '5507806f0045fe3e0e532da6',
#             '5507806f0045fe3e0e532dac',
#             '550780700045fe3e0e532dad',
#             '550780700045fe3e0e532daf',
#             '550780700045fe3e0e532db0',
#             '550780710045fe3e0e532db8',
#             '550780710045fe3e0e532db9',
#             '550780710045fe3e0e532dbe',
#             '550780710045fe3e0e532dc1',
#             '550780710045fe3e0e532dc4',
#             '550780710045fe3e0e532dc5',
#             '550780720045fe3e0e532dc7',
#             '550780720045fe3e0e532dc8',
#             '550780720045fe3e0e532dcb',
#             '550780750045fe3e0e532de9',
#             '550780750045fe3e0e532dea',
#             '550780860045fe3e0e532e87',
#             '550780860045fe3e0e532e8b',
#             '5507834d0045fe3da7c06f03',
#             '5507834d0045fe3da7c06f04',
#             '5507834d0045fe3da7c06f06',
#             '5507c3a70045fe3da7c06f28',
#             '550a624a0045fe3e0e532ffd',
#             '550a624b0045fe3e0e533002',
#             '550a624e0045fe3e0e53301c',
#             '550a624f0045fe3e0e533021',
#             '550a8aa30045fe3e0e533071',
#             '550a8aa80045fe3e0e5330a3',
#             '550a8aa80045fe3e0e5330a4',
#             '550a8aa80045fe3e0e5330a6',
#             '550a8aab0045fe3e0e5330d1',
#             '550a8ab10045fe3e0e533116',
#             '550a8ab40045fe3e0e533130',
#             '550a8ab50045fe3e0e53313f',
#             '550b79d00045fe3e0e533171',
#             '550b7cdb0045fe3e0e5331bc',
#             '550bb1b70045fe3e0e533230',
#             '550bb3960045fe3e0e533265',
#             '550bdcf30045fe3da7c07034',
#             '550bde790045fe3e0e5332ce',
#             '5513bca60045fe3e0e533357',
#             '5513bca60045fe3e0e53335c',
#             '5513bca70045fe3e0e533364',
#             '5513bca80045fe3e0e53336a',
#             '5513bca90045fe3e0e53337b',
#             '5513bcb40045fe3e0e5333d0',
#             '5513bcb40045fe3e0e5333d4',
#             '5513bcbb0045fe3e0e533403',
#             '5513bcbb0045fe3e0e53340c',
#             '5513bcc40045fe3e0e533438',
#             '5513bcc40045fe3e0e53343d',
#             '5513bccb0045fe3e0e53347f',
#             '5513bcd60045fe3e0e5334d8',
#             '5513bcda0045fe3e0e5334f1',
#             '5513bcdb0045fe3e0e5334f7',
#             '5513bf5c0045fe3da87d215f',
#             '5513c06f0045fe3da87d2172',
#             '5513c0dc0045fe3da7c070b5',
#             '5513c1070045fe3da7c070cc',
#             '551919710045fe3da7c070eb',
#             '551919820045fe3da7c070ef',
#             '551ca0b70045fe6e582cad95',
#             '551ca0b70045fe6e582cad96',
#             '551ca0b70045fe6e582cad97',
#             '551ca0b70045fe6e582cad98',
#             '551ca0b70045fe6e582cad99',
#             '551ca0b70045fe6e582cad9a',
#             '551ca0b80045fe6e582cad9b',
#             '551ca0b80045fe6e582cad9c',
#             '551ca0b80045fe6e582cad9d',
#             '551ca0b80045fe6e582cad9e',
#             '551ca0b80045fe6e582cad9f',
#             '551ca0b80045fe6e582cada0',
#             '551ca0b80045fe6e582cada1',
#             '552348ec0045fe6e582caf8c',
#             '5524d1440045fe6e582cafaf',
#             '5524d1d60045fe3da87d21b0',
#             '5525f38b0045fe6e582cb061',
#             '55274ac80045fe6e582cb1f1',
#             '55274aea0045fe6e582cb1fe',
#             '55274aeb0045fe6e582cb1ff',
#             '552765680045fe3da87d2200',
#             '552b5ebf0045fe3da7c07163',
#             '5530a38c0045fe6e582cb4f0',
#             '5530a38c0045fe6e582cb4f1',
#             '5530a38c0045fe6e582cb4f2',
#             '5530a38c0045fe6e582cb4f4',
#             '5530a38e0045fe6e582cb500',
#             '5530a38f0045fe6e582cb504',
#             '5530a4270045fe3da7c0718e',
#             '5530a4270045fe3da7c07190',
#             '5534b2f70045fe6e582cb58c',
#             '5534b51a0045fe3da7c071de',
#             '5534bfbe0045fe6e582cb5f6',
#             '5534bfbe0045fe6e582cb5f8',
#             '5534bfde0045fe6e582cb608',
#             '553f1a690045fe6e582cb9ed',
#             '55407ea70045fe6e582cba20',
#             '55485b5a0045fe6e582cbb89',
#             '555311c05417d13987d03f52',
#             '555311c15417d13987d03f59',
#             '555315bd5417d13987d03f6f',
#             '55531d795417d13987d03f81',
#             '55531d795417d13987d03f85',
#             '55531dd35417d13987d03f99',
#             '5553fe795417d13987d03fa3',
#             '5553fe795417d13987d03fa5',
#             '5553fe795417d13987d03fab',
#             '5553fe795417d13987d03fae',
#             '555401df5417d13987d03fb8',
#             '555401df5417d13987d03fba',
#             '555401df5417d13987d03fbd',
#             '555401df5417d13987d03fbf',
#             '55755f885417d16229e6009f',
#             '558a48205417d1251ce27135',
#             '5591fe235417d1251ce271ef',
#             '5591fe235417d1251ce271f6',
#             '5591fe235417d1251ce271f7',
#             '5591fe7d5417d1251ce2720a',
#             '559621be5417d1251ce274ba',
#             '559621be5417d1251ce274bb',
#             '559621be5417d1251ce274bc',
#             '559621be5417d1251ce274bd',
#             '559621be5417d1251ce274be',
#             '559621be5417d1251ce274c0',
#             '559621be5417d1251ce274c1',
#             '559621be5417d1251ce274c2',
#             '559621be5417d1251ce274c3',
#             '559621be5417d1251ce274c4',
#             '559624f95417d120a8c6a3e8',
#             '559624f95417d120a8c6a3e9',
#             '559624f95417d120a8c6a3ea',
#             '559624f95417d120a8c6a3eb',
#             '559624f95417d120a8c6a3ec',
#             '559624fa5417d120a8c6a3ed',
#             '559624fa5417d120a8c6a3ee',
#             '559624fa5417d120a8c6a3ef',
#             '559624fa5417d120a8c6a3f0',
#             '559624fa5417d120a8c6a3f1',
#             '559624fa5417d120a8c6a3f2',
#             '559624fa5417d120a8c6a3f3',
#             '559b41e75417d120a74278c2',
#             '559c97525417d1489003e90c',
#             '559dfcdb5417d1489003e942',
#             '559dfcdb5417d1489003e943',
#             '559dfcdc5417d1489003e944',
#             '559dfcdc5417d1489003e945',
#             '559dfcdc5417d1489003e946',
#             '559dfcdc5417d1489003e947',
#             '559dfcdc5417d1489003e948',
#             '559dfcdc5417d1489003e949',
#             '559dfcdc5417d1489003e94a',
#             '559dfcdc5417d1489003e94b',
#             '559dfcdc5417d1489003e94c',
#             '559dfcdc5417d1489003e94d',
#             '559dfcdc5417d1489003e94e',
#             '559dfcdc5417d1489003e94f',
#             '559dfcdc5417d1489003e950',
#             '559dfcdc5417d1489003e951',
#             '55a37bab5417d147b19c0752',
#             '55a37bab5417d147b19c0753',
#             '55a37bab5417d147b19c0754',
#             '55a37bab5417d147b19c0755',
#             '55a37bac5417d147b19c0756',
#             '55a37bac5417d147b19c0757',
#             '55a37bac5417d147b19c0758',
#             '55a37bac5417d147b19c0759',
#             '55a37bac5417d147b19c075a',
#             '55a744af5417d143a5e5890f',
#             '55a8b1d75417d143a5e589bc',
#             '55adf53c5417d145335850be',
#             '55af4afc5417d143a5e58b31',
#             '55c330a75417d143a5e58dd9',
#             '563aac425417d16ef86e9a63',
#             '563aac845417d16f0c6d313f',
#             '564eb17b5417d16c4a3dccb7',
#             '565274775417d16ef86e9cb8',
#             '5680eab15417d10768a09d40',
#             '569c974b5417d108050164a8',
#             '569c974b5417d108050164b6',
#             '569c9ddb5417d108050164f7',
#             '569e02575417d1080501665e',
#             '569e03fb5417d10805016684',
#             '569e04eb5417d108050166a5',
#             '569e11b25417d108050166ba',
#             '569e11b25417d108050166bc',
#             '56c691275417d1080501888d',
#             '56cabafa5417d10805018af1',
#             '56d54d4d5417d108050195df',
#             '56d54d4d5417d108050195e5',
#             '56d54d6b5417d108050195ee',
#             '56d54f515417d10c6d3c6e24',
#             '56d54f925417d10c6d3c6e29',
#             '56d54feb5417d10c6d3c6e2e',
#             '56d54feb5417d10c6d3c6e2f',
#             '56d54feb5417d10c6d3c6e30',
#             '56d54feb5417d10c6d3c6e31',
#             '56f7a7f85417d175d17511e3',
#             '56f7a8d05417d175d075127d',
#             '56f7a9bf5417d175d17511ec',
#             '56f7aa375417d175d0751285',
#             '56f7aabc5417d175d17511f0',
#             '56f7abe65417d175d0751289',
#             '56f7acd05417d175d075128d',
#             '56f7add95417d175d1751215',
#             '56f7ae8a5417d175d1751219',
#             '56f7af0a5417d175d175121d',
#             '56f7af865417d175d1751225',
#             '56f7b0265417d175d1751229',
#             '56f7b0cf5417d175d175122d',
#             '56f7b19e5417d175d07512b6',
#             '56f7b3e85417d175d1751232',
#             '56f7b53e5417d175d1751236',
#             '56f7cdfe5417d175d0751373',
#             '56f7cfdf5417d175d0751377',
#             '56f7d0795417d175d17512f3',
#             '56f7d1675417d175d075138b',
#             '56f7d1dc5417d175d17512f7',
#             '56f7d2515417d175d17512fb',
#             '56f7d2d05417d175d17512ff',
#             '56f7d32d5417d175d1751303',
#             '56f7d3ad5417d175d0751393',
#             '56f7d42f5417d175d1751307',
#             '56f7d4f45417d175d1751310',
#             '56f7d5785417d175d075139c',
#             '56f7d5d75417d175d07513a4',
#             '56f7d62b5417d175d07513a8',
#             '56f7d6e05417d175d07513b0',
#             '56f7d7a85417d175d07513b4',
#             '570489e15417d156e034b4be',
#             '570db9035417d156e034ba80',
#             '570f3bb25417d166b6d4cdf5',
#             '570f46225417d166b6d4cdf9',
#             '570f692fdef29750303683b7',
#             '5718e1bfdef2977c21a5c41e',
#             ]


item_ids = ['537dcbade138230941ea18aa']


def do_items(item_ids, subject):
    tex = template
    dbname = subject
    for item_id in item_ids:
        tex += item_latex_render(ObjectId(item_id))
    tex += '\\end{document}'
    return tex


item_id = '559202d35417d1251ce2724b'
subject = 'klx_math'
path = paper_path
f = open('{}{}.tex'.format(path, '111111111'), 'w')
f.write(do_items(item_ids, subject))
f.close
