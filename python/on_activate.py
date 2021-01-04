import os, sys, sqlite3
from domino.core import log, Version
from domino.account import Account, find_account
from domino.databases.oracle import Databases, domino_login
from domino.cli import print_warning, print_error, print_comment, Console
from domino.crontab import CronTab
from domino.server import Server

TNAME = 'W2POS#CHECKS'

def table_exists(cur, name):
    cur.execute('select count(*) from tab where tname=:0',[name])
    count = cur.fetchone()[0]
    return count > 0 

def drop_table(cur):
    if table_exists(cur, TNAME):
        q = f'''
            drop table {TNAME}
            '''
        cur.execute(q)
        print(f'Удалена таблица "{TNAME}"')

def create_structure(account):
    database = Databases().get_database(account.id)
    if database is None:
        print_error('Не определена база данных')
        return
    print(f'{database.uri}')
    conn = database.connect()
    #print(f'{conn}')
    
    with conn:
        #print(account.id)
        domino_login(conn)
        cur = conn.cursor()
        q = f"update db1_agent set F43122705='{account.id}' where id = DOMINO.StringToDominoUID('4:0:0:1')"
        cur.execute(q)
       
        print(f'Учетная запись "{account.id}" записана в базу данных')
        #drop_table(cur)

        if not table_exists(cur, TNAME):
            q = f'''
            CREATE TABLE {TNAME}
            (
                Q_DEPT_UID  VARCHAR2(40 CHAR),
                Q_DATE      VARCHAR2(40 CHAR),
                Q_FR_UID    VARCHAR2(40 CHAR),
                Q_FR_SMENA  VARCHAR2(40 CHAR),
                Q_FR_NUMBER VARCHAR2(40 CHAR),
                DEPT_ID     RAW(8),
                CTL_ID      RAW(8),
                CHECK_NO    VARCHAR2(40 CHAR),
                CHECK_DATE  DATE,
                CARDS       NUMBER,
                PRODUCTS    NUMBER,
                P_START     DATE,
                P_TIME      VARCHAR2(40 CHAR),
                PID         NUMBER,
                THREAD      NUMBER,
                INFO        VARCHAR2(2000 CHAR)
            )
            '''
            print(f'Создана таблица "{TNAME}"')
            cur.execute(q)
            #q = f'''
            #create unique index {TNAME}_BY_CHECK on {TNAME}(Q_DEPT_UID, Q_DATE, Q_FR_UID, Q_FR_SMENA, Q_FR_NUMBER)
            #'''
            #cur.execute(q)
            #print(f'Создан уникальный индекс')

if __name__ == "__main__":
    c = Console()
    version_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    account = find_account(c.arg(1))
    if account is None:
        sys.exit()

    try:
        create_structure(account)
    except BaseException as ex:
        log.exception(f'on_activate {account}')
        print_error(f'Ошибка при создании структур данных для {account.id} : {ex}')
