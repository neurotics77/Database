import time

def decorator(func):
	def wrapper(*args,**kvargs):
		start_time=time.time()#----->函数运行前时间
		func(*args,**kvargs)
		end_time=time.time()#----->函数运行后时间
		cost_time=end_time-start_time#---->运行函数消耗时间
		print("消耗时间为%.5fs"%cost_time)
		return cost_time
	return wrapper#---->装饰器其实是对闭包的一个应用