import command
import random
import numpy
cmd = command.CMD()

cmd.run()

# import joblib
# print(joblib.load(r'OurDB\test\tables_attr.dbi'))

#file = open('delete_sql.txt','w')
# file.write("create database test;\
# use test;\n\
# create table t1;\n\
# id int\n\
# name char(100)\n\
# ;\n")
# file.write("use t1;\n")
# a = numpy.linspace(1,1000,1000)
# random.shuffle(a)
# for i in range (1000):
#     # 插入
#     # file.write("insert table t1;\n")
#     # file.write(str(i+1)+" abcf;\n")
#     # 更新
#     # file.write("update table t1;\n")
#     # file.write(str(random.randint(1,1001)) + "\n")
#     # file.write("name " + str(random.randint(1,1001)) + "abcf\n")
#     # 查询
#     # file.write("select from t1;\n")
#     # file.write(str(random.randint(1,1000)) + "\n")
#     # 删除
#     file.write("delete from t1;\n")
#     file.write(str(random.randint(1,1001))+"\n")
# file.write("exit;")
