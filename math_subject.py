#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Create Date: 2016-06-21 15:01
# Author: Airlam

import os
import re
from bson.objectid import ObjectId
from subject import Subject

# from maths.kcode_render_latex import normalize_latex, punc_in_img, template


template = ur'''% !TEX encoding=utf8
% !TEX program=xelatex
\documentclass{standalone}'''u'''
\\usepackage{xeCJK}
\\usepackage{varwidth}
\\usepackage{amsmath, amssymb}
\\usepackage{yhmath}
\\usepackage{graphicx}
\\usepackage{pifont}
\\usepackage{ifthen}'''ur'''
\setCJKmainfont{SimSun}
\setlength{\fboxsep}{0pt}
\setlength{\fboxrule}{0pt}
\newcommand{\dq}{\mbox{(\quad)}.}
\newcommand{\fourch}[4]
{\begin{tabular}{*{4} {@{} p{0.25\textwidth}}} A. #1 & B. #2 & C. #3 & D. #4 \end{tabular}}
\newcommand{\twoch}[4]
{\begin{tabular}{*{2} {@{} p{0.5\textwidth}}} A. #1 & B. #2\\ \end{tabular}
\begin{tabular}{*{2} {@{} p{0.5\textwidth}}}C. #3 & D. #4 \end{tabular}}
\newcommand{\onech}[4]{ A. #1 \\ B. #2 \\ C. #3 \\ D. #4}
\newcommand{\imgch}[4]
{\newline \begin{tabular}{cccc}  \fbox{#1} &  \fbox{#2} & \fbox{#3} &  \fbox{#4} \\ A & B & C & D \end{tabular}}
\newlength{\cha}
\newlength{\chb}
\newlength{\chc}
\newlength{\chd}
\newlength{\maxw}
\setlength{\parindent}{0em}
\newcommand{\ch}[4]
{
\settowidth{\cha}{A. #1 }
\settowidth{\chb}{B. #2 }
\settowidth{\chc}{C. #3 }
\settowidth{\chd}{D. #4 }
\setlength{\maxw}{\cha}
\ifthenelse{\lengthtest{\chb > \maxw}}{\setlength{\maxw}{\chb}}{}
\ifthenelse{\lengthtest{\chc > \maxw}}{\setlength{\maxw}{\chc}}{}
\ifthenelse{\lengthtest{\chd > \maxw}}{\setlength{\maxw}{\chd}}{}
\ifthenelse{\lengthtest{\maxw > 0.48\textwidth}}
{\onech{#1}{#2}{#3}{#4}}
{\ifthenelse{\lengthtest{\maxw > 0.24\textwidth}}{\twoch{#1}{#2}{#3}{#4}}{\fourch{#1}{#2}{#3}{#4}}}}
\newcommand{\dd}{\rule[-.2ex]{6em}{.5pt}}
\newcounter{nqq}
\newcommand{\wqq}{\stepcounter{nqq}\thenqq.\quad}
\begin{document}
'''


def normalize_latex(ori):

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
        col_arg = 'c' * col_num
        return re.sub(ur'{c+}', '{%s}' % col_arg, x.group(0))

    def split_mathmode(x):
        x = re.sub(ur'split', ur'aligned', x.group(0))
        return x

    def circled_num(s):
        circled2ding = [
            (ur'\u2460', ur'\text{\ding{172}}'),
            (ur'\u2461', ur'\text{\ding{173}}'),
            (ur'\u2462', ur'\text{\ding{174}}'),
            (ur'\u2463', ur'\text{\ding{175}}'),
            (ur'\u2464', ur'\text{\ding{176}}'),
            (ur'\u2465', ur'\text{\ding{177}}'),
            (ur'\u2466', ur'\text{\ding{178}}'),
            (ur'\u2467', ur'\text{\ding{179}}'),
            (ur'\u2468', ur'\text{\ding{180}}'),
            (ur'\u2469', ur'\text{\ding{181}}'),
        ]
        for uni, latex in circled2ding:
            s = s.replace(uni, latex)
        return s

    # ori = ori.replace('\n', '\\\\\n')
    ori = ori.replace('\\overparen', '\\wideparen')
    ori = ori.replace('\\lt', '<')
    ori = ori.replace('\\gt', '>')
    ori = ori.replace(u'\u007f', '')
    ori = ori.replace(ur'{align}', ur'{matrix}')
    ori = re.sub(ur'(?<!\\)%', '\%', ori)
    ori = cn_in_mathmode(ori)
    ori = re.sub(
        ur'\\begin{array}[\s\S]*?\\end{array}', array_col_correction, ori)
    ori = re.sub(
        ur'\\begin\s?{split}[\s\S]*?\\end\s?{split}', split_mathmode, ori)
    ori = re.sub(ur'\u005f\u005f+', ur'\\dd ', ori)
    ori = circled_num(ori)
    return ori


def punc_in_img(s):  # by ningshuo
    def _deal(s):
        stop = s.find(ur'[[/img]]')
        assert stop != -1
        result = re.sub(ur'\uff0e', ur'.', s[:stop])
        result = re.sub(ur'\uff1a', ur':', result)
        result = re.sub(ur'\uff0c', ur',', result)
        return result + s[stop:]

    s = re.split(ur'\[\[img\]\]', s)
    # print s, len(s)
    for idx, str in enumerate(s[1:], start=1):
        # print 'str', str
        s[idx] = _deal(str)
    s = ur'[[img]]'.join(s)
    return s


def get_opts_head(opts, img_file_re):
    opt_imgs_cnt = 0
    for opt in opts:
        opt = punc_in_img(opt)
        opt_imgs = re.findall(img_file_re, opt)
        if opt_imgs:
            opt_imgs_cnt += 1
    if opt_imgs_cnt == 4:
        return '\\imgch '
    else:
        return '\\ch '


class Math(Subject):

    def __init__(self, mongodb_host, db_name, image_dir_path, width_map=None):
        super(Math, self).__init__(mongodb_host, db_name, image_dir_path)

    def render_item_2_latex(self, item_id, width):
        if not ObjectId.is_valid(item_id):
            return ''
        item_id = ObjectId(item_id)
        item = self.db.items.find_one({'_id': item_id})
        if item is None:
            return ''
        img_re2 = re.compile(ur'\[\[img\]\].*?\[\[/img\]\]')
        img_file_re = re.compile(ur'\w+\.(?:png|jpg|gif|bmp)')

        tex_list = list()
        if item['data']['type'] == 1001:
            tex = item['data']['qs'][0]['desc']
            tex_list.append(normalize_latex(tex.replace('[[nn]]', '\\dq ')))

            opts = item['data']['qs'][0]['opts']
            opt_tex = get_opts_head(opts, img_file_re)
            for opt in opts:
                opt = punc_in_img(opt)
                opt_imgs = re.findall(img_file_re, opt)
                if opt_imgs:
                    # for index in range(len(opt_imgs)):
                    for image_file_name in opt_imgs:
                        # opt += '\\includegraphics{%s}\\ ' % opt_imgs[index]
                        image_file_path = os.path.join(self.image_dir_path,
                                                       image_file_name[:2], image_file_name[2:4], image_file_name)
                        opt += u'\\includegraphics[width=0.22\\textwidth]{{{}}}\\ '.format(
                            image_file_path)
                opt_tex += u'{%s}' % opt
            tex_list.append(normalize_latex(opt_tex))

        elif item['data']['type'] == 1002:
            tex = item['data']['qs'][0]['desc']
            tex_list.append(normalize_latex(tex.replace('[[nn]]', '\\dd ')))

        elif item['data']['type'] == 1003:
            if item['data']['stem']:
                item['data']['stem'] = punc_in_img(item['data']['stem'])
                item['data']['stem'] = item['data'][
                    'stem'].replace('[[nn]]', '\\dd ')
                tex_list.append(normalize_latex(item['data']['stem']))

            for qs in item['data']['qs']:
                if qs['desc']:
                    tex = u'\\indent \\wqq {}'.format(qs['desc'])
                    tex_list.append(normalize_latex(
                        tex.replace('[[nn]]', '\\dd ')))

        tex = u'\\\\\n'.join(tex_list)
        tex = re.sub(img_re2, u'', tex)
        buffer_head = u'\\begin{varwidth}{%smm}\n' % width
        buffer_content = u'% {}\n{}\n'.format(str(item_id), tex)
        buffer_footer = u'\\end{varwidth}\n\\end{document}'
        ret_str = template
        ret_str += buffer_head
        ret_str += buffer_content
        ret_str += buffer_footer
        return ret_str

    def render_item_in_paper_2_latex(self, paper_id, width_map):
        paper_id = ObjectId(paper_id)
        paper = self.db.papers.find_one({'_id': paper_id})

        result = dict()
        for part in paper['parts']:
            for item in part:
                item_id = str(item['item_id'])
                item_type = item['type']
                latex_of_item = self.render_item_2_latex(
                    item_id, width_map[item_type])
                result[item_id] = latex_of_item

        return result
