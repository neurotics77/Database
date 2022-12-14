from Operations import DatabaseOperations, TableOperations
from utils import decorator
import joblib
import atexit
import os
import pandas as pd
# from typing import


class CMD:
    dbs_index:      dict = {}  # {'db_name':{'path':relative_path..}}
    cur_tables:     dict = {}  # {'tb_name':record_size}
    cur_tbs_attr:   dict = {}  # {'tb_name+attr_name':{tb_name,type,length,column}}

    db_path: str = 'OurDB'
    dbs_index_path: str = 'OurDB/dbs_index.dbi'
    tables_name: str = 'tables_name.dbi'
    tbs_attr_name : str = 'tables_attr.dbi'
    cur_tbs_name: str = None
    cur_db_path: str = None

    cur_cmd: str = ''

    def __init__(self) -> None:
        if os.path.exists(self.dbs_index_path):
            self.load_db_index()
        atexit.register(self.save_db_index)
        atexit.register(self.save_tables)
        atexit.register(self.save_tbs_attr)

    def run(self):
        while True:
            tips = f"OurDB/{self.cur_tbs_name}> " if self.cur_tbs_name is not None else "OurDB> "
            code = input(tips)
            self.parse(code)

    def parse(self, code: str):
        if len(code) == 0:
            return
        for c in code:
            if c in ['(', ')', ',']:
                self.cur_cmd += ' ' + c + ' '
            else:
                self.cur_cmd += c
        if code[-1] == ';':
            _cur_cmd = self.cur_cmd[:-1].split()
            if _cur_cmd[0].lower() == 'create' and len(_cur_cmd)==3:
                if _cur_cmd[1].lower() == 'database':  # 创建数据库
                    self.create_db(_cur_cmd[2])
                elif _cur_cmd[1].lower() == 'table':   # 创建表
                    field_info = []
                    while True:
                        feild = input(f"请输入表{_cur_cmd[2]}的属性> ")
                        if feild == ';':
                            break
                        field_info.append(tuple(feild.split()))
                    TableOperations.create(_cur_cmd[2], field_info, self.cur_db_path, self.cur_tables, self.cur_tbs_attr)
                    self.save_tables()


            elif _cur_cmd[0].lower() == 'delete' and len(_cur_cmd)>=3:
                if _cur_cmd[1].lower() == 'database': # 删除数据库
                    self.del_db(_cur_cmd[2])
                elif _cur_cmd[1].lower() == 'table': # 删除表
                    pass
                elif _cur_cmd[1].lower() == 'from': # 删除表中的元组
                    table_name = _cur_cmd[2]
                    field_info = [int(input('请输入id的值> '))]
                    TableOperations.delete(table_name, self.cur_db_path, field_info, self.cur_tables)

            elif _cur_cmd[0] == 'select':
                table_name = _cur_cmd[2]
                field_info = [int(input('请输入id的值> '))]
                TableOperations.retrieve(table_name, field_info, self.cur_db_path, self.cur_tbs_attr)

            elif _cur_cmd[0].lower() == 'insert':
                table_name = _cur_cmd[2]
                values = []
                while True:
                    _values = input("请输入值> ")
                    if _values[-1] == ';':
                        values.extend(_values[:-1].split())
                        break
                    values.extend(_values.split())
                TableOperations.insert(table_name, values, self.cur_db_path, self.cur_tables, self.cur_tbs_attr)

            elif _cur_cmd[0].lower() == 'show' and len(_cur_cmd) >= 2: 
                if _cur_cmd[1].lower() == 'database': # 列出所有数据库 show database;
                    self.show_dbs()
                elif _cur_cmd[1].lower() == 'table': # 列出所有表 show table;
                    pass
                elif len(_cur_cmd) == 4 and _cur_cmd[2].lower() == 'from': # 列出某个数据库中的所有表 show table from test1;
                    pass

            elif _cur_cmd[0].lower() == 'update':
                if _cur_cmd[1].lower() == 'table':
                    table_name = _cur_cmd[2]
                    _id = int(input('请输入id> '))
                    field_info = input('请输入属性和新值> ').split()
                    TableOperations.update(table_name, field_info, _id, self.cur_db_path, self.cur_tbs_attr)

            elif _cur_cmd[0].lower() == 'use': # 切换数据库
                self.switch_db(_cur_cmd[1])
            elif _cur_cmd[0].lower() == 'exit':
                if self.cur_tbs_name is not None: # 退出数据库
                    self.cur_tbs_name, self.cur_db_path = None, None
                else: # 退出程序
                    exit()
            else:
                print("未知指令。")
            self.cur_cmd = ''

    @decorator    
    def show_dbs(self):
        print('*'*20)
        for ds_name, info in self.dbs_index.items():
            print('*\t', ds_name)
        print('*'*20)

    @decorator
    def create_db(self, db_name: str) -> None:
        '''创建一个数据库'''
        path = f'{self.db_path}/{db_name}'
        if DatabaseOperations.create(path):
            self.dbs_index[db_name] = {'path':path}
            self.cur_db_path = path
            self.save_tables()
            self.save_tbs_attr()
            self.cur_db_path = None
        else:
            print(f"创建数据库{db_name}失败。")
    
    @decorator
    def del_db(self, db_name: str) -> None:
        path = f'{self.db_path}/{db_name}'
        if DatabaseOperations.delete(path):
            del self.dbs_index[db_name]
        else:
            print(f"删除数据库{db_name}失败。")
    
    @decorator
    def switch_db(self, db_name: str):
        '''切换数据库'''
        self.save_tables()
        try:
            db_path = self.dbs_index[db_name]['path']
            if os.path.exists(db_path):
                self.cur_tbs_name = db_name
                self.cur_db_path = db_path
                if self.cur_db_path is not None:
                    self.load_tables()
        except KeyError:
            print(f'没有名为{db_name}的数据库。')

    def save_db_index(self):
        joblib.dump(self.dbs_index, self.dbs_index_path)
        # pd.DataFrame(self.dbs_index).T.to_csv(self.dbs_index_path)

    def save_tables(self):
        if self.cur_db_path is not None:
            joblib.dump(self.cur_tables, f'{self.cur_db_path}/{self.tables_name}')
            # pd.DataFrame(self.cur_tables).T.to_csv(f'{self.cur_db_path}/{self.tables_name}')
    
    def save_tbs_attr(self):
        if self.cur_db_path is not None:
            joblib.dump(self.cur_tbs_attr, f'{self.cur_db_path}/{self.tbs_attr_name}')
            # pd.DataFrame(self.cur_tables).T.to_csv(f'{self.cur_db_path}/{self.tbs_attr_name}')

    def load_db_index(self):
        self.dbs_index = joblib.load(self.dbs_index_path)
    
    def load_tables(self):
        if os.path.exists(f'{self.cur_db_path}/{self.tables_name}'):
            self.cur_tables = joblib.load(f'{self.cur_db_path}/{self.tables_name}')
        # self.cur_tables = pd.read_csv(f'{self.cur_db_path}/{self.tables_name}').to_dict()

    def load_tbs_attr(self):
        if os.path.exists(f'{self.cur_db_path}/{self.tbs_attr_name}'):
            self.cur_tbs_attr = joblib.load(f'{self.cur_db_path}/{self.tbs_attr_name}')
        # self.cur_tables = pd.read_csv(f'{self.cur_db_path}/{self.tbs_attr_name}').to_dict()


    def exit():
        '''退出程序'''
        pass

