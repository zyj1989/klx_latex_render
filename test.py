#!/usr/bin/env python
# encoding:utf-8
'''
试卷渲染
'''

class ArithmeticSequence(object):
    """docstring for ArithmeticSequence"""
    def __init__(self, start=0, step=1):
        # super(ArithmeticSequence, self).__init__()
        self.start = start
        self.step = step
        self.change = {}
    def __getitem__(self, key):
        try:
            return self.change[key]
        except KeyError:
            return self.start + key*self.step
    def __setitem__(self, key, value):
        self.change[key] = value

class Rectangle(object):
    """docstring for Rectangle"""
    def __init__(self):
        self.size = [0, 0]
    def setSize(self, size):
        self.size = size
    def getSize(self):
        return self.width, self.height
a = Rectangle()
a.setSize((10,50))
print a.width
print a.size
