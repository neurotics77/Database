1. create database: 
   - load databases.dbi 
    +名字：路径
    save databases.dbi 

2. use database：
   - load databases.dbi 
    查 名字 对 路径
    cd 路径

   - create tables.dbi （表名：记录大小）
   - create attributes.dbi（属性名: 表名， 属性类型，长度，列数）


3. create tables（属性1， 属性2， 属性3）：
   - load tables.dbi 
    +名字 : 记录大小
    save tables.dbi 

   - create  {table}_block.dbi （块地址: 块大小， 块剩余大小）

   - load attributes.dbi
    +属性1：表名，属性类型，长度（byte），列数
    +属性2：表名，属性类型，长度（byte），列数；
    +属性3：表名，属性类型，长度（byte），列数
    save attribute.dbi

   - create  {table}_index.dbi （id【主码】:块名字， 第几行， 有效位）

4. insert into table values (值1【主码】， 值2， 值3);：
- 判断主码是否重复：
   - 遍历{table}_indexs中的主码
   - 重复：报错
- 找可以用的块

load {table}_blocks.dbi （块地址， 块大小（4kb）， 块剩余大小）

   - 查可以插入的块 blockn（n.csv）

如果没有：
+块地址：块大小， 表名， 块剩余大小， 
如果块剩余大小 <记录大小：

else：

   - 对应的记录 块剩余大小-=记录大小

save {table}_blocks.dbi

- 把记录插入到块n.csv

load n.csv
直接插
save n.csv

- 为记录建立索引

load {table}_index.dbi （id【主码】:块名字， 第几行）

   - + 值1：block地址（n.csv），（块大小-剩余大小）/记录大小

save {table}_index.dbi

方法二：
遍历{table}_indexs，找到一个不有效的索引（块地址，第几行）
索引改为 id： 块地址，第几行， 有效
块地址，第几行 插入新的记录

5. delete from table where (属性x【主码】==值)：
   - 遍历{table}_indexs中的主码：

找到对应的主码：块地址，第几行 ，标注不有效

   - 更新块剩余大小：

{table}_block 根据 块地址 找 块记录：
 块剩余大小+=记录大小

6. update table set （属性x=值）where （id=值）
   - 遍历{table}_indexs中的主码：

找到对应的主码：块地址，第几行，

   - 根据attributes.dbi 属性x 找在第几列
   - 更新 属性值
8. select * from table where （id=值）
   - 遍历{table}_indexs中的主码：

找到对应的主码：块地址，第几行

   - 按照块地址（n.csv）取出那一行数据





