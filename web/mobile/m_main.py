#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('..')

import tornado.web
from model import manager as mgr
from lib import *
from m_base import *

class MobileIndexHandler(MobileBaseHandler):

    def get(self):
        self._tpl['top'] = []
        self.mrender('m_index.html')

class MobileLoginHandler(MobileBaseHandler):

    def get(self):
        self._tpl['ref'] = self.ref
        self.mrender('m_login.html')

    def post(self):
        userid = self.get_argument('userid', None)
        origref = self.get_argument('ref', None)
        if userid.isalpha():
            passwd = self.get_argument('password')
            res = mgr.auth.login(userid, passwd, self.remote_ip)
            if hasattr(res, 'userid') and res.userid.lower() == userid.lower():
                self.set_secure_cookie('userid', userid)
                self.set_secure_cookie('sessionid', str(res.seid))
                if origref and 'login' not in origref: self.redirect(origref)
                else: self.redirect('/m/')
        self._tpl['msg'] = u'用户名或密码错误'
        self._tpl['ref'] = origref
        self.mrender('m_login.html')

class MobileLogoutHandler(MobileBaseHandler):

    def get(self):
        userid = self.current_user
        if not userid:
            self.redirect('/m/')
        sid = self.get_secure_cookie('sessionid')
        mgr.auth.logout(sid)
        self.clear_all_cookies()
        self.redirect('/m/') 

class MobileBoardHandler(MobileBaseHandler):

    def get(self):
        sections = mgr.section.get_all_section()
        for s in sections:
            # todo: filter those userid has not perm
            s['boards'] = mgr.board.get_by_sid(s.sid)

        self._tpl['sections'] = sections
        self.mrender('m_board.html')

class MobilePostHandler(MobileBaseHandler):

    page_size = 25

    def get(self, boardname, start = 0):

        if not boardname.isalpha():
            return m_error(self, u'版面不存在')
        
        board = mgr.board.get_board(boardname)
        bid = mgr.board.name2id(boardname)
        total = mgr.post.get_posts_total(bid)

        start = int(start) if start else 0

        # todo: if has_read_perm

        self.page_size = self.__class__.page_size
        if start == 0: # 0 means the last pid
            start = total - self.page_size
            if start < 0: start = 0

        plist = mgr.post.get_posts(bid, start, self.page_size)

        for p in plist:
            p.unread = 1 if mgr.readmark.is_read(self.userid, \
                    boardname, p.pid) else 0

        self._tpl['plist'] = plist
        self._tpl['board'] = board

        prev = start - self.page_size
        if prev < 0: prev = None

        next = start + self.page_size
        if next > total: next = None

        self._tpl['prev'] = prev
        self._tpl['next'] = next

        self.mrender('m_listpost.html')

class MobileNewPostHandler(MobileBaseHandler):

    def get(self, boardname):
        if not self.userid: self.login_page()
        board = None if not boardname.isalpha() else mgr.board.get_board(boardname)
        if not board: m_error(self, u'没有这个版哦～')

        self._tpl['board'] = board
        self.mrender('m_newpost.html')

    def post(self, boardname):
        if not self.userid: self.login_page()

        board = None if not boardname.isalpha() else mgr.board.get_board(boardname)
        if not board: m_error(self, u'错误的讨论区')

        # todo: if has post perm
        title = fa( self.get_argument('title'))
        content = self.get_argument('content')

        res = mgr.action.new_post(boardname = boardname, \
                userid = self.userid,\
                title=title,\
                content = content,\
                addr = self.remote_ip,\
                host = 'TestLand',
                replyable=1)

        msg = u'发表成功' if res else u'发表失败'
        self.set_secure_cookie('msg', msg)
        self.redirect('/m/%s' % boardname)

class MobileThreadHandler(MobileBaseHandler):

    def get(self, boardname, pid):

        board = None if not boardname.isalpha() \
                else mgr.board.get_board(boardname)
        if not board:
            m_error(self, u'错误的讨论区')

        # todo: if has read perm
        post = mgr.post.get_post(pid)
        if not post:
            m_error(self, u'本帖子不存在或已被删除')
        tid = post.tid
        bid = mgr.board.name2id(boardname)
        total = mgr.post.get_posts_topic_total(bid)
        plist = mgr.post.get_posts_onetopic(tid, bid, 0, total)

        self._tpl['board'] = board
        self._tpl['plist'] = plist
        self.mrender('m_read.html')

class MobileFavHandler(MobileBaseHandler):

    def get(self):
        if not self.userid: self.login_page()
        all_fav = mgr.favourite.get_all(self.userid)
        boards = [mgr.board.get_board_by_id(bid) \
                for bid in all_fav]
        for b in boards:
            pid = mgr.post.get_last_pid(b.boardname)
            if pid is None: pid = -1
            b.unread = not mgr.readmark.is_read(self.userid, b.boardname, pid)
        self._tpl['boards'] = boards
        self.mrender('m_fav.html')

class MobileMailHandler(MobileBaseHandler):

    page_size = 5
    def get(self, start = 0):

        if not self.userid: self.login_page()

        start = int(start) if start else 0
        total = mgr.mail.get_mail_total(self.userid)

        if start == 0: # 0 means the last pid
            start = total - self.page_size
            if start < 0: start = 0

        mlist = mgr.mail.get_mail(self.userid, start, self.page_size)

        self._tpl['mlist'] = mlist

        prev = start - self.page_size
        if prev < 0: prev = None

        next = start + self.page_size
        if next > total: next = None

        self._tpl['prev'] = prev
        self._tpl['next'] = next

        self.mrender('m_listmail.html')

    def post(self, startmid = 0):

        if not self.userid:  self.login_page()
        title = self.get_argument('title')
        touserid = self.get_argument('touserid')
        content = self.get_argument('content')
        try:
            replyid = self.get_argument('replyid')
        except:
            replyid = ''

        # todo: check if userid is in mail blacklist 

        if replyid == '':
            res = mgr.action.send_mail(self.userid, \
                    touserid, \
                    title = title,\
                    content = content,\
                    fromaddr = self.remote_ip)
        else:
            old_mail = mgr.mail.one_mail(replyid)
            res = mgr.action.reply_mail(self.userid,\
                    old_mail,\
                    title = title,\
                    content = content,\
                    fromaddr = self.remote_ip)
        msg = u'发送成功' if res else u'发送失败'
        self.set_secure_cookie('msg', msg)
        self.redirect('/m/mail/')

class MobileSendMailHandler(MobileBaseHandler):

    def get(self, replyid = 0):

        if not self.userid: self.login_page()
        replyid = int(replyid) if replyid else 0
        uid = mgr.userinfo.name2id(self.userid)

        mail = {}
        if replyid != 0:
            old_mail = mgr.mail.one_mail(replyid)
            if old_mail.title[:3] != 'Re:':
                old_mail.title ='Re:'  + old_mail.title
            mail['title'] = old_mail.title
            mail['touserid'] = old_mail.fromuserid
            mail['quote'] = fun_gen_quote(old_mail.fromuserid, old_mail.content)
            mail['replyid'] = old_mail.mid
        else:
            mail = {'title':'', 'touserid':'', 'content':'',\
                    'replyid': '', 'quote': ''}

        self._tpl['mail'] = mail
        self.mrender('m_sendmail.html')

class MobileDataHandler(MobileBaseHandler):

    def get(self):
        self.mrender('m_data.html')

class MobileAboutHandler(MobileBaseHandler):

    def get(self):
        self.mrender('m_about.html')



