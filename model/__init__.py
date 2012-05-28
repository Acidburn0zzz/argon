import MySQLdb
import cPickle
import config

from Model import Manager

def init_database():
    for table_name in config.BASE_TABLE :
        init_table(table_name)

def init_table(table_name):
    from globaldb import global_conn as db
    with open(config.SQL_TPL_DIR+'argo_'+table_name+'.sql') as f:
        sql = f.read()
        print sql
        db.execute(sql)

class CF:

    from globaldb import global_conn,global_cache
    from Model import Section,Online,UserInfo,UserAuth,Board
    
    db = global_conn
    ch = global_cache

    section   = Section()
    online    = Online(max_login=3)
    userinfo  = UserInfo()
    auth      = UserAuth(userinfo,online)
    board     = Board()
    
    loads = [section,online,userinfo,auth,board]

    use = {
        "section":section,
        "online":online,
        "auth":auth,
        "board":board,
        }

manager = Manager(CF)
