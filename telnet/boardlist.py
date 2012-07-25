# -*- coding: utf-8 -*-
import sys
sys.path.append('../')

from chaofeng import ascii as ac
from chaofeng.g import mark
from chaofeng.ui import PagedTable#,HiddenInput#,AppendTable#SimpleTable,
from model import manager
from argo_frame import AuthedFrame
from libtelnet import zh_format_d
from view import TextBoxFrame
import config

class BaseTableFrame(AuthedFrame):

    ### Handler

    def top_bar(self):
        raise NotImplementedError

    def quick_help(self):
        raise NotImplementedError
    
    def print_thead(self):
        raise NotImplementedError

    def notify(self, msg):
        raise NotImplementedError

    def get_default_index(self):
        raise NotImplementedError

    def get_data(self, start, limit):
        raise NotImplementedError

    def wrapper_li(self, li):
        raise NotImplementedError

    def load_table(self):
        table = self.load(PagedTable, self.get_data, self.wrapper_li,
                          self.get_default_index(),
                          start_line=4, page_limit=20)
        return table        

    def initialize(self):
        super(BaseTableFrame, self).initialize()
        self.table = self.load_table()
        self.restore()

    def bottom_bar(self):
        self.render('bottom')

    def message(self, msg):
        self.session.message = msg
        self.write(ac.move2(24, 1))
        self.render('bottom_msg', message=msg)
        self.table.restore_cursor_gently()

    def restore(self):
        self.cls()
        self.top_bar()
        self.quick_help()
        self.print_thead()
        self.bottom_bar()
        self.table.goto(0)        ###############   Ugly!!!
        self.table.restore_screen()

    def get(self, data):
        if data in ac.ks_finish:
            self.finish()
        self.table.do_command(config.hotkeys['table_table'].get(data))
        self.do_command(config.hotkeys['table'].get(data))

    def readline(self, acceptable=ac.is_safe_char, finish=ac.ks_finish, buf_size=20, prompt=u'', prefix=''):
        self.write(''.join((ac.move2(24,1),  ac.kill_line)))
        res = super(BaseTableFrame, self).readline(acceptable, finish, 
                                                   buf_size, prompt, prefix=prefix)
        self.write('\r')
        self.bottom_bar()
        self.table.restore_cursor_gently()
        return res

    def readnum(self, prompt=''):
        no = self.readline(acceptable=lambda x:x.isdigit(),
                           buf_size=8,  prompt=prompt)
        if no is not False :
            return int(no) - 1
        else :
            return False

    def read_with_hook(self, hook, buf_size=20, prompt=''):
        self.write(''.join((ac.move2(2,1),
                            ac.kill_line)))
        if prompt:
            self.write(prompt)
        buf = []
        while len(buf) < buf_size:
            ds = self.read_secret(2)
            ds = ds or ds[0]
            if ds == ac.k_backspace:
                if buf:
                    data = buf.pop()
                    self.write(ac.backspace)
                continue
            elif ds in ac.ks_finish:
                break
            elif ds == ac.k_ctrl_c:
                buf = False
                break
            else:
                if ds.isalnum() :
                    buf.append(ds)
                    self.write(ds)
                    hook(''.join(buf))
        self.write('\r')
        self.quick_help()
        self.table.restore_cursor_gently()
        if buf is False :
            return buf
        else:
            return ''.join(buf)                

class BaseBoardListFrame(BaseTableFrame):

    boards = []

    def top_bar(self):
        self.render('top')
        self.writeln()
        
    def quick_help(self):
        self.writeln(config.str['BOARDLIST_QUICK_HELP'])

    def print_thead(self):
        self.writeln(config.str['BOARDLIST_THEAD'])

    def notify(self, msg):
        self.write(ac.move2(0, 1))
        self.render('top_msg', messages=msg)
        self.table.restore_cursor_gently()

    def get_default_index(self):
        raise NotImplementedError

    def get_data(self, start, limit):
        raise NotImplementedError
    
    def wrapper_li(self, li):
        return self.render_str('boardlist-li', **li)

    def get(self, data):
        if data in ac.ks_finish:
            self.finish()
        self.table.do_command(config.hotkeys['g_table'].get(data))
        self.table.do_command(config.hotkeys['boardlist_table'].get(data))
        self.do_command(config.hotkeys['boardlist'].get(data))

    def finish(self):
        self.suspend('board', board=self.table.fetch())

    ######################

    def goto_last(self):
        self.table.goto(self.board_total-1)

    def goto_line(self):
        no = self.readnum()
        if no is not False:
            self.table.goto(no)
        else:
            self.table.refresh_cursor_gently()
            self.message(u'放弃输入')

    def goto_with_prefix(self,prefix):  # // Ugly but work.
        data = self.boards
        for index,item in enumerate(data):
            if item['boardname'].startswith(prefix):
                self.write(ac.save)
                self.table.restore_cursor_gently()
                self.table.goto(index)
                self.write(ac.restore)
                return
            
    def search(self):
        self.read_with_hook(hook = lambda x : self.goto_with_prefix(x) ,
                            prompt=u'搜寻讨论区：')
        self.table.restore_cursor_gently()

    def sort(self, mode):
        if mode == 1 :
            self.boards.sort(key = lambda x: \
                                manager.online.board_online(x['boardname'] or 0),
                            reverse=True)
        elif mode == 2:
            self.boards.sort(key = lambda x: x['boardname'])
        elif mode == 3:
            self.boards.sort(key = lambda x: x['description'])
        else:
            self.boards.sort(key = lambda x:x['bid'])
        self.table.goto(self.table.fetch_num())

    def change_sort(self):
        self.sort_mode += 1
        if self.sort_mode > 3 :
            self.sort_mode = 0
        self.sort(self.sort_mode)
        self.restore()
        self.message(config.str['MSG_BOARDLIST_MODE_%s'%self.sort_mode])

    def watch_board(self):
        self.suspend('query_board', board=self.table.fetch())

    def add_to_fav(self):
        manager.favourite.add(self.userid, self.table.fetch()['bid'])
        self.message(u'预定版块成功！')

    def remove_fav(self):
        manager.favourite.remove(self.userid, self.table.fetch()['bid'])
        self.message(u'取消预定版块成功！')

@mark('boardlist')
class NormalBoardListFrame(BaseBoardListFrame):

    def get_default_index(self):
        return 0

    def get_data(self, start, limit):
        return self.boards[start:start+limit]

    def load_boardlist(self):
        if self.sid is None:
            self.boards = manager.board.get_all_boards()
        else:
            self.boards = manager.board.get_by_sid(self.sid)
        self.board_total = len(self.boards)

    def initialize(self, sid=None):
        self.sid = sid
        self.load_boardlist()
        self.sort_mode = 0
        super(NormalBoardListFrame, self).initialize()

@mark('favourite')
class FavouriteFrame(BaseBoardListFrame):

    def get_default_index(self):
        return 0

    def get_data(self, start, limit):
        data = manager.favourite.get_all(self.userid)
        data = map(lambda d : manager.board.get_board_by_id(d),
                   data)
        return data

@mark('board')
class BoardFrame(BaseTableFrame):

    def top_bar(self):
        self.writeln(self.render_str('top'))

    def quick_help(self):
        self.writeln(config.str['BOARD_QUICK_HELP'])

    def print_thead(self):
        self.write(self.thead)

    def notify(self, msg):
        self.write(ac.move2(0, 1))
        self.render('top_msg', messages=msg)
        self.table.restore_cursor_gently()

    def get_default_index(self):
        return 0

    def get_data(self, start, limit):
        return self.data_loader(start, limit)

    def wrapper_li(self, li):
        return self.render_str('board-li', **li)

    def get(self, data):
        if data in ac.ks_finish:
            self.finish()
        self.table.do_command(config.hotkeys['g_table'].get(data))
        self.table.do_command(config.hotkeys['board_table'].get(data))
        self.do_command(config.hotkeys['board'].get(data))

    def initialize(self, board):
        self.board = board
        self.boardname = board['boardname']
        manager.action.enter_board(self.userid, self.seid, self.boardname)
        self.session.lastboard = board
        self.set_view_mode(0)
        super(BoardFrame, self).initialize()

    ##########

    def clear(self):
        manager.action.exit_board(self.userid, self.seid, self.boardname)

    mode_thead = ['NORMAL', 'GMODE', 'MMODE', 'TOPIC', 'ONETOPIC', 'AUTHOR']

    def set_view_mode(self, mode):
        if mode == 1:
            data_loader = lambda o,l : manager.post.get_posts_g(self.boardname, o, l)
        elif mode == 2:
            data_loader = lambda o,l : manager.post.get_posts_m(self.boardname, o, l)
        elif mode == 3:
            data_loader = lambda p,l : manager.post.get_posts_topic(self.boardname, p, l)
        elif mode == 4:
            data_loader = lambda p,l : manager.post.get_posts_onetopic(self.tid, self.boardname,p,l)
        elif mode == 5:
            data_loader = lambda p,l : manager.post.get_posts_owner(self.author, self.boardname,p,l)
        else :
            data_loader = lambda o,l : manager.post.get_posts(self.boardname, o, l)
        self.data_loader = data_loader
        self.thead = config.str['BOARD_THEAD_%s' % self.mode_thead[mode]]
        self.mode = mode

    def finish(self):
        pid = self.table.fetch()['pid']
        if pid is not None:
            self.suspend('post', boardname=self.boardname, pid=pid)

    #####################

    def goto_line(self):
        no = self.readnum(prompt=u"跳转到哪篇文章？")
        if no is not False:
            self.table.goto(no)
        else:
            self.table.refresh_cursor_gently()
            self.message(u'放弃输入')

    def get_last_pid(self):
        return manager.post.get_last_pid(self.boardname)

    def goto_last(self):
        self.table.goto(self.get_last_pid())

    def change_mode(self):
        if self.mode >=3 : mode=0
        else : mode = self.mode+1
        self.set_view_mode(mode)
        self.table.goto(0)  #!!!  Ugly but work.
        self.restore()
        self.message(config.str['MSG_BOARD_MODE_%s' % self.mode_thead[self.mode]])

    ###############
    # Edit/Reply  #
    ###############

    def new_post(self):
        # if manager.perm.has_new_post_perm(self.userid, self.boardname):
        self.suspend('new_post', board=self.board)

    def reply_post(self):
        p = self.table.fetch()
        self.suspend('reply_post', boardname=self.boardname, post=p)

    def edit_post(self):
        p = self.table.fetch()
        self.suspend('edit_post', boardname=self.boardname, post=p)

    def edit_title(self):
        p = self.table.fetch()
        title = self.readline(prompt=u'新标题：',prefix=p['title'])
        p['title'] = title
        manager.action.update_title(self.userid,self.boardname,
                                    p['pid'], title)
        self.table.set_hover_data(p)
        
#     def del_post(self):
#         pass

#     def reproduced(self):
#         pass

    def goto_tid(self):
        self.tid = self.table.fetch()['tid']
        self.set_view_mode(4)
        self.table.goto(0)    #!!!! ugly too.
        self.restore()

    def goto_author(self):
        self.author = self.table.fetch()['owner']
        self.set_view_mode(5)
        self.table.goto(0)    #!!!! ugly too.
        self.restore()

    def goto_back(self):
        if self.mode != 0 :
            self.set_view_mode(0)
            self.restore()
            return
        super(BoardFrame, self).goto_back()

    def clear_readmark(self):
        last = self.get_last_pid()
        manager.readmark.clear_unread(self.userid, self.boardname, last)
        self.restore()

    def set_read(self):
        p = self.table.fetch()
        manager.readmark.set_read(self.userid, self.boardname, p['pid'])
        self.table.set_hover_data(p)

    def set_g_mark(self):
        p = self.table.fetch()
        p['flag'] = p['flag'] ^ 1
        manager.post.update_post(self.boardname, p['pid'], flag=p['flag'])
        self.set_hover_data(p)

    def set_g_mark(self):
        p = self.table.fetch()
        p['flag'] = p['flag'] ^ 2
        manager.post.update_post(self.boardname, p['pid'], flag=p['flag'])
        self.set_hover_data(p)

    def query_author(self):
        user = self.table.fetch()
        self.suspend('query_user', user)        

@mark('query_board')
class QueryBoardFrame(TextBoxFrame):

    def get_text(self):
        return self.render_str('board-t', **self.board)
    
    def initialize(self, board):
        self.board = board
        super(QueryBoardFrame, self).initialize()

    def finish(self,a=None):
        self.goto_back()

    def add_to_fav(self):
        manager.favourite.add(self.userid, self.board['bid'])
        self.message(u'预定版块成功！')

    def get(self, data):
        super(QueryBoardFrame, self).get(data)
        self.do_command(config.hotkeys['view-board'].get(data))
