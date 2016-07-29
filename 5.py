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
from func import show_pretty_dict


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
    elif img_info['size_w'] > 180:  # img display real
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
            text = text_opr(text)
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
            s = re.sub(ur'[\u4e00-\u9fa5,\u3001,\u2103,\u2191,\u2193]+',
                       lambda x: ur'\text{%s}' % x.group(), s)
            unicode_cor = [
                (ur'\u2264', ur'\leqslant '),
                (ur'\u2265', ur'\geqslant '),
            ]
            for k, v in unicode_cor:
                s = s.replace(k, v)
            return s

        def text_opr(s):
            # latex_remaining_char = ['$', '%', '&', '#', '^', '_', ]
            s = re.sub(ur'(?<!\\)\$', u'\\$', s)
            s = re.sub(ur'(?<!\\)%', u'\\%', s)
            s = re.sub(ur'(?<!\\)&', u'\\&', s)
            s = re.sub(ur'(?<!\\)#', u'\\#', s)
            s = re.sub(ur'(?<!\\)\^', u'\\^', s)
            s = re.sub(ur'(?<!\\)_', u'\\_', s)
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
            (ur'\u2460', ur'{\text{\ding{172}}}'),  # circled numbers
            (ur'\u2461', ur'{\text{\ding{173}}}'),
            (ur'\u2462', ur'{\text{\ding{174}}}'),
            (ur'\u2463', ur'{\text{\ding{175}}}'),
            (ur'\u2464', ur'{\text{\ding{176}}}'),
            (ur'\u2465', ur'{\text{\ding{177}}}'),
            (ur'\u2466', ur'{\text{\ding{178}}}'),
            (ur'\u2467', ur'{\text{\ding{179}}}'),
            (ur'\u2468', ur'{\text{\ding{180}}}'),
            (ur'\u2469', ur'{\text{\ding{181}}}'),
            (ur'\u00a0', ur' '),
            (ur'\overparen', ur'\wideparen'),
            (ur'\lt', ur'<'),
            (ur'\gt', ur'>'),
            (ur'\u007f', ur''),
            (ur'{align}', ur'{matrix}'),
            (ur'{split}', ur'{aligned}'),
            (ur'\uff1d', ur'='),
            (ur'\u2550', ur'='),
            (ur'\Omega', ur'\text{$\Omega$}'),
            (ur'\style{font-family:Times New Roman}{g}', ur'\textsl{g}'),
            (ur'_\rm', ur'_\phrm'),
            (ur'^\rm', ur'^\phrm'),
            (ur'[[nn]]', ur'\dd '),
            (ur'\u200b', ur''),
            (ur'\uff1c', ur'<'),
            (ur'\uff1e', ur'>'),
            (ur'\ufe63', ur'-'),
            (ur'\downarrow', ur'\downarrow{}'),
            (ur'->', ur' ->'),
            (ur'<=>', ur' <=>'),
            (ur'<-', ur' <-'),
            (ur'？', ur'?'),
            (ur'\u00ad', ur''),
        ]
        for uni, latex in unicode2latex:
            s = s.replace(uni, latex)
        return s

    def unicode_chem_cor(ori):
        ori = re.sub(ur'\s*?}', ur'}', ori)
        ori = re.sub(ur'(?<!(?:-|=))>', lambda x: ur'\gt{} ', ori)
        ori = re.sub(ur'<(?!(?:-|=))', lambda x: ur'\lt{} ', ori)
        return ori

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
    ori = unicode_chem_cor(ori)
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


def get_opts_head(opts):
    opt_imgs_cnt = 0
    opt_imgs_inline_cnt = 0
    if len(opts) == 3:
        result = '\\trech'
    elif len(opts) == 5:
        result = '\\fivch'
    elif len(opts) == 4:
        for opt in opts:
            opt = str2latex(opt)
            opt_imgs = re.findall(img_file_re, opt)
            opt_imgs_inline = re.findall(
                ur'\[\[inline\]\].*?\[\[/inline\]\]', opt)
            if opt_imgs:
                opt_imgs_cnt += 1
            if opt_imgs_inline:
                opt_imgs_inline_cnt += 1

        if opt_imgs_cnt == 4 and opt_imgs_inline_cnt != 4:
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
            im = Image.open(file_path_name)
            arg = 'width'
            if im.size[0] < im.size[1]:
                # adjust the longer one between width end height
                arg = 'height'
            opt_img = '\\includegraphics[{}={}\\optwidth]{{{}}}'.format(
                arg, img_width, img_file)
    opt = re.sub(img_re3, '', opt)
    return [opt, opt_img]


def deal_desc_img(desc):
    result = {
        'text': '',
        'imgs': '',
    }
    s = desc
    img_inpar = re.findall(ur'\[\[inpar\]\](.*?)\[\[/inpar\]\]', s)
    desc_text = re.sub(ur'\[\[inpar\]\](.*?)\[\[/inpar\]\]', u'', s)
    desc_text = re.sub(
        ur'\[\[inline\]\](.*?)\[\[/inline\]\]', lambda x: x.group(1), desc_text)
    desc_text = re.sub(  # only valid for one img ---
        ur'\[\[display\]\](.*?)\[\[/display\]\]', lambda x: u'\\begin{displayimgs}%s\\end{displayimgs}' % x.group(1), desc_text)
    img_inpar = u'\\ '.join(img_inpar)

    result['imgs'] = img_inpar
    result['text'] = desc_text
    return result


def deal_with_opt(opt, img_width, opts_head):

    if opts_head == '\\imgch':
        opt_text = re.sub(img_display_pattern, '', opt)
        opt_text = re.sub(img_inpar_pattern, '', opt_text)
        opt_text = re.sub(img_inline_pattern, '', opt_text)
        opt_imgs = re.findall(ur'\]\](.*?)\[\[/', opt)
        opt_imgs = u''.join(opt_imgs)
        size_w = re.findall(ur'\[width=(.*?)pt', opt_imgs)
        size_h = re.findall(ur',height=(.*?)pt\]', opt_imgs)
        size_w = float(u''.join(size_w))
        size_h = float(u''.join(size_h))
        # print size_w, size_h
        arg = 'width'
        if size_w < size_h:
            # adjust the longer one between width end height
            arg = 'height'
        opt_imgs = re.sub(ur'\[.*?\]', ur'[%s=%s\\optwidth]' %
                          (arg, img_width), opt_imgs)

    else:
        opt_imgs = []
        opt = re.sub(img_inline_pattern, lambda x: x.group(1), opt)
        opt = re.sub(img_display_pattern, lambda x: x.group(1), opt)
        opt = re.sub(img_inpar_pattern, lambda x: x.group(1), opt)
        opt_text = opt
    # print [opt_text, opt_imgs]
    opt_text = opt_text.replace(u'\\par', u'\\\\ ')
    return [opt_text, opt_imgs]


def deal_with_qs(qs, item_type):
    if item_type not in [1001, 1002, 2001, 2002]:
        print '========'
        show_pretty_dict(qs['desc'])
        desc_tex = str2latex(qs['desc'])
        qs_tex = deal_desc_img(desc_tex)
        opts = qs['opts']
        opt_tex = get_opts_head(opts)
        for opt in opts:
            opt = get_opt_img(opt, 0.222)
            opt_tex += '{%s}{%s}' % (opt[0], opt[1])
        qs_tex['text'] += str2latex(opt_tex)
    return qs_tex


def item_latex_render(item_id):
    item = db.items.find_one({'_id': item_id})
    qs_tex = u''
    if not item:
        return '%%%%%%%%%%%%%%%%'
    tex = '\r%% {} {}\r'.format(
        item_id, item['data']['type'])
    if item['data']['type'] in [1001, 2001, 1002, 2002, 4001, 4002]:
        tex += '\\begin{questions}'
        qs = item['data']['qs'][0]
        if qs['desc'] == '' and item['data']['stem'] != '':
            desc = item['data']['stem']
        else:
            desc = qs['desc']
        desc = str2latex(desc)
        desc = deal_desc_img(desc)
        opts = qs['opts']
        opts_head = get_opts_head(opts)
        opt_tex = opts_head
        for opt in opts:
            opt = str2latex(opt)
            opt = deal_with_opt(opt, 0.222, opts_head)
            opt_tex += '{%s}{%s}' % (opt[0], opt[1])
        opt_tex = str2latex(opt_tex)
        tex += u'\\klxitemm{%s}{%s%s}' % (desc['imgs'],
                                          desc['text'], opt_tex)

    elif item['data']['type'] in [1003, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 4003, 4004, 3003, 3004]:
        tex += '\\begin{questions}\n'  # begin of an item
        # tex += '{{{}}}'.format(width_map[1003])
        if len(item['data']['stem']) == 0:
            if len(item['data']['qs']) == 1:
                qs = item['data']['qs']
                stem_buffer = deal_desc_img()
                tex += deal_with_qs(qs, item['data']['type'])
            else:
                for qs in item['data']['qs']:
                    qss_tex = u''
                    if len(qs['desc']) != 0:
                        qs_buffer = deal_with_qs(qs, item['data']['type'])
                        qs_tex += u'\\klxqs{%s}{%s' % (
                            qs_buffer['imgs'], qs_buffer['text'])
                    if 'qs' in qs:
                        for qss in qs['qs']:
                            qss_buffer = deal_with_qs(
                                qss, item['data']['type'])
                            qss_tex += u'\\klxqss{%s}{%s}' % (
                                qss_buffer['imgs'], qss_buffer['text'])
                    qs_tex += qss_tex
                    qs_tex += ur'}'
                tex += qs_tex
        else:
            print 'yes'
            stem_buffer = deal_desc_img(str2latex(item['data']['stem']))
            print str2latex(item['data']['stem'])
            tex += u'\\klxitemm{%s}{%s' % (
                stem_buffer['imgs'], stem_buffer['text'])
            if len(item['data']['qs'][0]['desc']) != 0:
                for qs in item['data']['qs']:
                    qss_tex = u''
                    if len(qs['desc']) != 0:
                        show_pretty_dict(qs)
                        qs_buffer = deal_with_qs(qs, item['data']['type'])
                        show_pretty_dict(qs_buffer)
                        qs_tex += u'\\klxqs{%s}{%s' % (
                            qs_buffer['imgs'], qs_buffer['text'])
                    if 'qs' in qs:
                        for qss in qs['qs']:
                            qss_buffer = deal_with_qs(
                                qss, item['data']['type'])
                            qss_tex += u'\\klxqss{%s}{%s}' % (
                                qss_buffer['imgs'], qss_buffer['text'])
                    qs_tex += qss_tex
                    qs_tex += ur'}'
                tex += qs_tex
        tex = re.sub(img_re3, u'', tex)
        tex += u'}'
    tex += u'\\end{questions}'  # end of an item
    if item['data']['type'] in [1001, 2001, 3001, 4001]:
        tex = tex.replace(ur'\dd ', ur'\dq ')
    return tex


def int2choice(s):
    if type(s) == list:
        for idx, i in enumerate(s, start=0):
            s[idx] = str(i)
        s = ''.join(s)

    elif type(s) == int:
        s = str(s)
    s = s.replace(ur'0', ur'A')
    s = s.replace(ur'1', ur'B')
    s = s.replace(ur'2', ur'C')
    s = s.replace(ur'3', ur'D')
    s = s.replace(ur'4', ur'E')
    return s


def itemans_latex_render(item_id):
    item = db.items.find_one({'_id': item_id})
    qs_tex = u''
    if not item:
        return '%%%%%%%%%%%%%%%%'
    tex = '\r%% {} {}\r'.format(item_id, item['data']['type'])
    if item['data']['type'] in [1001, 2001, 3001, 4001]:
        tex += '\\begin{questions}'
        qs = item['data']['qs'][0]
        if qs['exp'] == '':
            tex += u'\\end{questions}'
        else:
            exp = str2latex(qs['exp'])
            tex_buffer = u'解析' + exp
            tex += u'\klxitemm{}{%s}' % tex_buffer
            tex += u'\\end{questions}'
    return tex


def get_choice_ans(item_id):
    item = db.items.find_one({'_id': item_id})
    return int2choice(item['data']['qs'][0]['ans'])


def get_choice_anssheet(part):
    result = ''
    lines = []
    max_col = 10  # 10 for math , 5 for science subject
    max_qs = len(part)
    if max_qs < max_col:
        max_col = max_qs
    max_rows = max_qs / max_col
    last_row = max_qs % max_col
    rest = max_col - last_row
    col_speci = []
    for x in range(max_col):
        col_speci.append('c')
    col_speci = u'|'.join(col_speci)
    result = u'{\centering \\begin{tabular}{|%s|} \hline \r' % col_speci
    idx = []
    ans = []
    for i in range(max_qs):
        if i % max_col == 0 and i != 0:
            lines.append(u'&'.join(idx))
            lines.append(u'&'.join(ans))
            idx = []
            ans = []
        item = part[i]
        idx.append(str(i + 1))
        ans.append(get_choice_ans(item['item_id']))
    if max_col != max_qs:
        for i in range(rest):
            idx.append(u' ')
            ans.append(u' ')

    lines.append(u'&'.join(idx))
    lines.append(u'&'.join(ans))
    result += u'\\\\ \hline \r'.join(lines)
    result += u'\\\\ \hline \r \\end{tabular}\par}'
    return result


def klx_paper_render(paper):

    def _deal_paper_head(paper):
        return '%% {id}\n\\begin{{center}}\n{paper_name}\n\\end{{center}}'.format(id=paper['_id'], paper_name=paper['name'])

    def _deal_part_head(part):
        item_type = itmtyp_2_name[part[0]['type']]
        return u'\\wns{{{}}} \par \\nopagebreak \n'.format(item_type)

    result_tex = template
    result_tex += u'\\onecolumn \n '
    result_tex += _deal_paper_head(paper)
    for part in paper['parts']:
        result_tex += _deal_part_head(part)

        for item in part:
            result_tex += item_latex_render(item['item_id'])
    result_tex += u'\klxans{%s}' % paper['name']
    for part in paper['parts']:
        result_tex += _deal_part_head(part)
        if part[0]['type'] in [1001, 2001, 3001, 4001]:
            result_tex += get_choice_anssheet(part)
        for item in part:
            result_tex += itemans_latex_render(item['item_id'])
    result_tex += '\\end{document}'
    return result_tex


def get_items(item_ids, subject):
    tex = template
    dbname = subject
    for item_id in item_ids:
        # print item_id
        tex += item_latex_render(ObjectId(item_id))
        # tex += '\\\\'  # used for multi-items
    tex += u'\n\\end{document}'
    return tex


def do_multi_items_test(skip, limit):
    item_ids_cursor = db.items.find({'deleted': False,
                                     # 'data.type': 1001
                                     }, {
        '_id': 1}).skip(skip).limit(limit)
    item_ids = []
    for item in item_ids_cursor:
        item_ids.append(item['_id'])
    tex = get_items(item_ids, subject)
    f = open(os.path.join(paper_path, '{}.tex'.format(skip)), 'w')
    f.write(tex)
    f.close()
    # print skip


def do_certain_items(item_ids, subject):
    tex = get_items(item_ids, subject)
    f = open(os.path.join(paper_path, 'test.tex'), 'w')
    f.write(tex)
    f.close()


def do_paper_test(paper_id, subject):
    paper = db.papers.find_one({'_id': ObjectId(paper_id)})
    # print type(paper)
    tex = klx_paper_render(paper)
    file = os.path.join(paper_path, '{}.tex'.format(paper_id))
    f = open(file, 'w')
    f.write(tex)
    f.close
    return file


def compile_latex(file):
    command = 'xelatex -output-directory {dir} {file}'.format(
        dir=paper_path, file=file)
    os.system(command)
    command2 = 'open {file} -a Skim.app'.format(file=file[:-4] + '.pdf')
    os.system(command2)

"""
=== Setting =============================================================
"""
width_map = {
    1001: '175mm',
    1002: '175mm',
    1003: '175mm',
    2001: '175mm',
    2002: '175mm',
    2003: '175mm',
    2004: '175mm',
    2005: '175mm',
    2006: '175mm',
    2007: '175mm',
    2008: '175mm',
    2009: '175mm',
}

pdf_width = u'125.46652mm'
img_url = 'http://www.kuailexue.com/data/img/'

itmtyp_2_name = {1001: u'选择题',
                 1002: u'填空题',
                 1003: u'解答题',
                 2001: u'选择题',
                 2002: u'填空题',
                 2003: u'解答题',
                 2004: u'实验题',
                 2005: u'模块选做题',
                 2006: u'作图题',
                 2007: u'科普阅读题',
                 2008: u'简答题',
                 2009: u'计算题',
                 2010: u'综合应用题',
                 4001: u'选择题',
                 4002: u'填空题',
                 4003: u'非选择题',
                 4004: u'计算题'
                 }

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
img_file_re = re.compile(ur'\w+\.(?:png|jpg|gif|bmp|jpeg|tif)', re.I)
img_display_pattern = re.compile(ur'\[\[display\]\](.*?)\[\[/display\]\]')
img_inpar_pattern = re.compile(ur'\[\[inpar\]\](.*?)\[\[/inpar\]\]')
img_inline_pattern = re.compile(ur'\[\[inline\]\](.*?)\[\[/inline\]\]')
output_dir = '/Users/zhangyingjie/var/data/paper'

for path in [paper_path, item_path, img_path]:
    if os.path.exists(path):
        pass
    else:
        os.makedirs(path)


item_ids = [  # math
    '5368a442e13823417ff9bc67',
    '54364cb30045fe48f83730ee',
    '56d9474b5417d15b1626fe2e',
    '56de8abd5417d15e130f8bbf',
    '537dcc42e138230941ea408c',
    '537dcc42e138230941ea40a0',
]

item_ids = [
    # '56e91a9f5417d15b16270324',
    # '54d3175c0045fe3e0e531c94',
    # '53b4dab3e13823317fef6700',
    # '5359165ce1382357d4b0bf54',
    ObjectId("537dcb02e138230941e9f0e1")
]

# do_multi_items_test(56465, 500)
# do_certain_items(item_ids, subject)
paper_id = ObjectId("54db033827ffa92ff08080c0")
do_paper_test(paper_id, subject)
