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
img_re3 = re.compile(ur'\n?\s?\u200b?(\[\[img\]\].*?\[\[/img\]\])')
img_file_re = re.compile(ur'\w+\.(?:png|jpg|gif|bmp|jpeg)')
img_display_pattern = re.compile(ur'\[\[display\]\](.*?)\[\[/display\]\]')
img_inpar_pattern = re.compile(ur'\[\[inpar\]\](.*?)\[\[/inpar\]\]')
img_inline_pattern = re.compile(ur'\[\[inline\]\](.*?)\[\[/inline\]\]')


desc = u'利用计算器[[img]]{"src":"8253afe639af7dd55c4502177c62de02.png"}[[/img]]求 \( \sin 30^\circ \) 时，依次按键[[img]]{"src":"4b62a164e3086670c8f0269ba9076ecc.png"}[[/img]]则计算器上显示的结果是[[nn]]利用计算器求 \\( \\sin 30^\\circ \\) 时，依次按键[[img]]{\"src\": \"328dd2c165c9191e95070ccf47da7f7b.png\"}[[/img]]则计算器上显示的结果是 \\(\\left(\\[\qquad\\right)\\)'


s = ur'[[inline]]\ \raisebox{-pt}{{\includegraphics[]{1231}\ [[/inline]]'
x = re.sub(ur'(?<=includegraphics\[).*?(?=\]{)', 'xxx', s)
print x
