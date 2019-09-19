import datetime


log_file = 'errors.log'


def log(error_code, log_file=log_file):
	with open(log_file,'a') as f:
		now = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
		f.write(now)
		f.write(': ')
		f.write(error_code)
		f.write('\n')
	
