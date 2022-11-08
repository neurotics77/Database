from utils import decorator
import pandas as pd
from typing import Tuple,List
import shutil
import os
import sys
import joblib

BLOCK_SIZE = 4000

class DatabaseOperations:
    @staticmethod
    def create(database_path: str) -> bool:
        if os.path.exists(database_path):
            print("已经存在同名的数据库。")
            return False
        os.makedirs(database_path)
        return True
        
    @staticmethod
    def delete(database_path: str) -> bool:
        if os.path.exists(database_path):
            shutil.rmtree(database_path)
            return True
        return False


class TableOperations:
    
    # 每一个数据表下都有一个索引表，其块放在table_name/table_index文件目录下
    # 每当创建索引表的新块时，需要在table_name/table_blocks.dbi中添加块地址，块大小，剩余大小
    # 当前数据表的所有数据块放在table_name/data文件目录下
    @staticmethod
    def create(table_name: str, field_info: List[Tuple[str, str]],
            cur_db_path: str, cur_tables: dict, cur_tbs_attr: dict) -> None:

        # 计算记录的大小 更新 cur_tbs_attr 中的值
        record_size = 0
        for column_count, (name, attr) in enumerate(field_info, start=1):
            size = 0
            if attr=="int":
                size = 4
                record_size += 4
            elif 'char' in attr:
                tmp, size = attr.split('('), 1
                if len(tmp) > 1:# char(10)
                    size = int(tmp[-1][:-1])
                record_size += size
            # 更新 cur_tbs_attr 中的值
            cur_tbs_attr[f"{table_name}_{name}"] = [table_name, attr, size, column_count]

        # update cur_tables
        cur_tables[table_name] = record_size

        # 创建 {table_name}/table_index 文件夹
        # 创建 {table_name}/table_blocks.dbi
        # 创建 {table_name}/data 文件夹
        # 创建 {table_name}_1.csv
        # 创建 {table_name}/table_index/delete_table.dbi
        print(f'{cur_db_path}/{table_name}')
        if not os.path.exists(f'{cur_db_path}/{table_name}'):
            os.makedirs(f'{cur_db_path}/{table_name}')
        if not os.path.exists(f'{cur_db_path}/{table_name}/table_index'):
            os.makedirs(f'{cur_db_path}/{table_name}/table_index')
        if not os.path.exists(f'{cur_db_path}/{table_name}/table_blocks.dbi'):
            joblib.dump({}, f'{cur_db_path}/{table_name}/table_blocks.dbi')
        if not os.path.exists(f'{cur_db_path}/{table_name}/data'):
            os.makedirs(f'{cur_db_path}/{table_name}/data')
        TableOperations.save_table_blocks(f'{cur_db_path}/{table_name}', {})
        if not os.path.exists(f'{cur_db_path}/{table_name}/table_index/{table_name}_1.csv'):
            df = pd.DataFrame([[BLOCK_SIZE, None, None, None]])
            df.to_csv(f'{cur_db_path}/{table_name}/table_index/{table_name}_1.csv', index=False)
        if not os.path.exists(f'{cur_db_path}/{table_name}/delete_table.dbi'):
            joblib.dump([], f'{cur_db_path}/{table_name}/delete_table.dbi')

    @staticmethod
    def delete(table_name: str,cur_db_path: str, field_info: List, cur_tables: dict) -> None:
        haveindex = False
        if haveindex:
            # 加载删除表
            #delete_table = joblib.load(f'{cur_db_path}/{table_name}/delete_table.dbi')
            cur_tb_path = f'{cur_db_path}/{table_name}'
            table_indexs = os.listdir(f'{cur_tb_path}/table_index')
            for table_index in table_indexs:
                block = pd.read_csv(f'{cur_tb_path}/table_index/{table_index}')
                row = 1
                while(row < block.shape[0]):
                    # 键相等且信息有效
                    if block.iloc[row,0] == field_info[0] and block.iloc[row,3] == 1:
                        # 有效位置0
                        block.iloc[row,3] = 0
                        # 保存删除的位置和对应的索引表
                        # delete_table.append([block.iloc[row,1],block.iloc[row,2]])
                        # joblib.dump(delete_table, f'{cur_db_path}/{table_name}/delete_table.dbi')
                        # 保存
                        block.to_csv(f'{cur_tb_path}/table_index/{table_index}', index=False)
                        # 加载table_block
                        table_blocks = TableOperations.load_table_blocks(cur_tb_path)
                        # 获取表名以索引table_blocks
                        table_name = cur_tb_path.split('/')[-1]
                        # 更改table_blocks中的块剩余大小
                        table_blocks[str(block.iloc[row,1])][1] += cur_tables[table_name]
                        TableOperations.save_table_blocks(cur_tb_path, table_blocks)
                        #print("删除成功")
                        return
                    elif block.iloc[row,0] == field_info[0] and block.iloc[row,3] == 0:
                        return
                    row += 1
            print("删除失败")
        else:
            cur_tb_path = f'{cur_db_path}/{table_name}'
            data_indexs = os.listdir(f'{cur_tb_path}/data')
            for data_index in data_indexs:
                block = pd.read_csv(f'{cur_tb_path}/data/{data_index}')
                row = 0
                while(row < block.shape[0]):
                    # 键相等且信息有效
                    if block.iloc[row,0] == field_info[0]:
                        # 加载table_block
                        table_blocks = TableOperations.load_table_blocks(cur_tb_path)
                        # 获取表名以索引table_blocks
                        table_name = cur_tb_path.split('/')[-1]
                        # 更改table_blocks中的块剩余大小
                        table_blocks[data_index][1] += cur_tables[table_name]
                        TableOperations.save_table_blocks(cur_tb_path, table_blocks)
                        return
                    row += 1
            print("删除失败")
        

    @staticmethod
    def insert(table_name: str, field_info: List,
            cur_db_path: str, cur_tbs_index: dict, cur_tbs_attr: dict) -> None:
        
        # 判断主键是否重复 默认第一个属性为主键
        if None not in TableOperations.traversal_key(f'{cur_db_path}/{table_name}', int(field_info[0])):
            print("ERROR主键值重复")

        # 查找表的记录大小：
        # tables_name = TableOperations.load_tables_name(cur_db_path)
        # print("tbs_name ", tables_name)
        record_size = cur_tbs_index[table_name]


        # 找出可以用的块：
        table_blocks = TableOperations.load_table_blocks(f'{cur_db_path}/{table_name}')
        avail_block_addr = ""
        isFind = False
        avail_block_addr = f'{table_name}_data_0.csv' # 默认值
        # print('table_blocks', table_blocks)
        
        use_delete = False
         # 加载删除表
        delete_table = joblib.load(f'{cur_db_path}/{table_name}/delete_table.dbi')
        if bool(delete_table):
            use_delete = True
            # 插入的块地址
            avail_block_addr = delete_table[0][0]
            # 插入的位置
            insert_row = delete_table[0][1]
            table_blocks[str(delete_table[0][0])][1] -= record_size
            # 删除此空白记录
            del delete_table[0]
            joblib.dump(delete_table,f'{cur_db_path}/{table_name}/delete_table.dbi')
            isFind = True
        else:
            for addr, value in table_blocks.items():
                avail_block_addr = addr
                if value[1] > record_size:
                    # 更新块剩余大小
                    table_blocks[addr][1] -= record_size
                    isFind = True
                    break
        
        # 申请新的块
        if not isFind:
            cur_block_num = int(avail_block_addr.split('_')[-1].split('.')[0])+1
            pd.DataFrame(columns = list(range(len(field_info)))).to_csv(f'{cur_db_path}/{table_name}/data/{table_name}_data_{cur_block_num}.csv', index=False)
            avail_block_addr = f'{table_name}_data_{cur_block_num}.csv'
            table_blocks[avail_block_addr] = [BLOCK_SIZE, BLOCK_SIZE-record_size]
            
        # 保存table_blocks
        TableOperations.save_table_blocks(f'{cur_db_path}/{table_name}', table_blocks)

        # 向 data/可用csv路径中插入值
        data = pd.read_csv(f'{cur_db_path}/{table_name}/data/{avail_block_addr}')
        if not use_delete:
            insert_row = len(data)
        data.loc[insert_row] = field_info
        data.to_csv(f'{cur_db_path}/{table_name}/data/{avail_block_addr}', index=False)

        # 为记录建立索引
        # 寻找可用的索引块 
        isFind = False
        table_indexs = os.listdir(f'{cur_db_path}/{table_name}/table_index')
        avail_index_addr = ""
        cur_index_count = 0
        for table_index in table_indexs:
            block = pd.read_csv(f'{cur_db_path}/{table_name}/table_index/{table_index}')
            index_rest_size = block.iloc[0].values[0]
            if index_rest_size >= 8:
                avail_index_addr = table_index
                isFind = True
                break
            cur_index_count+=1

        # 没有找到可用索引块的话,新建索引块文件
        if not isFind:
            cur_index_count += 1
            df = pd.DataFrame([[BLOCK_SIZE, None, None, None]], columns=list(range(4)))
            df.to_csv(f'{cur_db_path}/{table_name}/table_index/{table_name}_{cur_index_count}.csv', index=False)
            avail_index_addr = f'{table_name}_{cur_index_count}.csv'

        # 向可用的索引块中插入索引
        index_block = pd.read_csv(f'{cur_db_path}/{table_name}/table_index/{avail_index_addr}')
        index_block.loc[0] = [index_block.iloc[0].values[0] - 8, None, None, None]
        index_block.loc[len(index_block)] = [field_info[0], avail_block_addr, data.shape[0], 1]
        index_block.to_csv(f'{cur_db_path}/{table_name}/table_index/{avail_index_addr}', index=False)
            

    @staticmethod
    def update(table_name: str, field_info: List, key: int, cur_db_path: str, cur_tbs_attr: dict) -> None:
        attr = {value[3]: key.split("_")[-1] for key, value in cur_tbs_attr.items() if value[0] == table_name}
        block_addr, row = TableOperations.traversal_key(f'{cur_db_path}/{table_name}', key)
        if block_addr is None or row is None:
            print("更新出错")
        else:
            # 数据所在的块
            select_data_block = pd.read_csv(f'{cur_db_path}/{table_name}/data/{block_addr}')
            # field_info[0]为属性，field_info[1]为新值
            idx = [k for (k,v) in attr.items() if v == "id"]
            select_data_block.iloc[int(row)-1,idx[0]] = field_info[1]
        
            select_data_block.to_csv(f'{cur_db_path}/{table_name}/data/{block_addr}', index=False)
            #print("更新成功")
        

    @staticmethod
    def retrieve(table_name: str, field_info: List,cur_db_path: str, cur_tbs_attr: dict) -> None:
        # attr = {}
        # for key,value in cur_tbs_attr.items():
        #     if value[0] == table_name:
        #         attr[value[3]] = key.split("_")[-1]
        attr = {value[3]: key.split("_")[-1] for key, value in cur_tbs_attr.items() if value[0] == table_name}
        block_addr, row = TableOperations.traversal_key(f'{cur_db_path}/{table_name}', field_info[0])
        if block_addr is None or row is None:
            print("查询出错")
        else:
            # 数据所在的块
            select_data_block = pd.read_csv(f'{cur_db_path}/{table_name}/data/{block_addr}')
            #for i in range(select_data_block.shape[1]):
                #print(attr[int(i+1)] + ":" + str(select_data_block.iloc[int(row)-1,i]))

    @staticmethod
    def load_table_blocks(cur_tb_path: str):
        if os.path.exists(f'{cur_tb_path}/table_block.dbi'):
            return joblib.load(f'{cur_tb_path}/table_block.dbi')

    @staticmethod
    def load_tables_name(cur_db_path: str):
        if os.path.exists(f'{cur_db_path}/tables_name.dbi'):
            return joblib.load(f'{cur_db_path}/tables_name.dbi')
    
    @staticmethod
    def save_table_blocks( cur_tb_path: str, cur_tb_block: dict):
        if cur_tb_path is not None:
            joblib.dump(cur_tb_block, f'{cur_tb_path}/table_block.dbi')

    @staticmethod
    def traversal_key1(cur_tb_path: str, key: int):
        table_indexs = os.listdir(f'{cur_tb_path}/table_index')
        for table_index in table_indexs:
            block = pd.read_csv(f'{cur_tb_path}/table_index/{table_index}')
            row = 1
            while(row < block.shape[0]):
                # 键相等且信息有效
                if block.iloc[row,0] == key and block.iloc[row,3] == 1:
                    # 块地址
                    #result["block_attr"] = block[row,1]
                    # 记录所在的行数
                    #result["data_row"] = block[row,2]
                    # 索引文件名字
                    #result["table_index_name"] = table_index
                    # 匹配
                    #result["row"] = row
                    return block.iloc[row,1],block.iloc[row,2] 
                row += 1
        return (None, None)

    @staticmethod
    def traversal_key(cur_tb_path: str, key: int):
        table_data_blocks = os.listdir(f'{cur_tb_path}/data')
        for table_data in table_data_blocks:
            block = pd.read_csv(f'{cur_tb_path}/data/{table_data}')
            row = 0
            while(row < block.shape[0]):
                # 键相等且信息有效
                if block.iloc[row,0] == key:
                    return table_data,row+1
                row += 1
        return (None, None)