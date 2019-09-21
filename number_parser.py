import error_logger
import numpy as np

verbose = False

def parse_number(parse_string,
	coercion_type=float,
	lstrip = '',
	rstrip = '',
	null=['-',],
	null_value=np.nan
	):
	'''
	try to parse text to a numerical format

	type is probably int or float or np.float64
	lstrip and rstrip are symbols to strip (rigidly) from the left or right,
	null is the expected null string where we yield null_value
	if we get unexpected input we replace with the null value
	and output to a log
	'''
	if parse_string in null:
		return (null_value)
	log_string = 'parse_number received string ' + parse_string
	if parse_string[:len(lstrip)] != lstrip:
		log_string += ' but expected it to begin with "'+lstrip+'"'
		error_logger.log(log_string)
		return (null_value)
	left_stripped = parse_string[len(lstrip):]
	if rstrip and left_stripped[-len(rstrip):] != rstrip:
		log_string += ' but expected it to end with "'+rstrip
		log_string += '" after stripping "'+lstrip
		log_string += '" from the beginning'
		error_logger.log(log_string)
		return (null_value)
	if rstrip:
		stripped = left_stripped[:-len(rstrip)]
	else:
		stripped = left_stripped
	try:
		ans = coercion_type(stripped)
		if verbose:
			print ('parsed',parse_string,'to',ans)
		return(ans)
	except:
		log_string += ' but expected it to coerce to type '+str(coercion_type)
		log_string += ' after stripping "'+lstrip
		log_string += '" from the beginning and "'+rstrip
		log_string += '" from the end'
		log_string += ' to obtain "'
		log_string += stripped
		log_string += '"'
		error_logger.log(log_string)
		raise
		return (null_value)
