#!/usr/bin/env python
# encoding:utf-8
'''
pdf generate
'''


from reportlab.pdfgen.canvas import Canvas
c = Canvas('../pdf/bottom_up1.pdf')
# c.rect(91.28647, 635.81819, 100, 100)
c.grid([100, 200, 300], [100, 200, 300])
c.showPage()
c.save()
