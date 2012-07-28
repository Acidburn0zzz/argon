# -*- coding: utf-8 -*-

__metaclass__ = type

import sys
sys.path.append('../')

from chaofeng.g import mark
from chaofeng.ui import Animation,ColMenu,VisableInput,EastAsiaTextInput,\
    CheckBox, RadioButton
import chaofeng.ascii as ac
from libframe import BaseTableFrame
from model import manager
from menu import SelectFrame
import config
import codecs

@mark('sys_edit_menu_background')
class EditMenuBackgroundFrame(SelectFrame):

    def initialize(self):
        real = config.menu_background.keys()
        text = config.menu_background.values()
        super(EditMenuBackgroundFrame, self).initialize(real, text, (3,10))

    def finish(self):
        hover = self.menu.fetch()
        self.suspend('edit_text', filename=hover, callback=self.save_to_file,
                     text=self.get_background(hover))

    def get_background(self, hover):
        with codecs.open('static/%s' % hover, 'r', 'utf8') as f:
            buf = f.readlines()
            text = u'\r\n'.join(buf)
        return text

    def save_to_file(self, text):
        print text

@mark('sys_set_boardattr')
class FormFrame(BaseTableFrame):

    def top_bar(self):
        raise NotImplementedError

    def quick_help(self):
        raise NotImplementedError

    def print_thead(self):
        raise NotImplementedError

    def notify(self, msg):
        raise NotImplementedError

    def get_default_index(self):
        return 0

    def get_data(self, start, limit):
        raise NotImplementedError

    def wrapper_li(self, li):
        raise NotImplementedError
