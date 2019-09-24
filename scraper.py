import requests
from requests_futures.sessions import FuturesSession

from error_logger import log

import exceptions

import os  
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys
import time
import random
from sysconfig import get_platform



delay = .4
js_sleep =.5


chosen_driver = 'chrome'
#chosen_driver = 'firefox'

if chosen_driver == 'chrome':
	from selenium.webdriver.chrome.options import Options
	chrome_options = Options()
	chrome_options.add_argument("--headless")  
	this_os = get_platform().split('-')[0]
	if this_os == 'macosx':
		chrome_options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
		chromedriver_path = os.path.abspath("chromedriver")
	elif this_os == 'linux':
		chrome_options.binary_location = '/usr/bin/google-chrome'
		chromedriver_path = '/usr/bin/chromedriver'

elif chosen_driver == 'firefox':
	from selenium.webdriver.firefox.options import Options
	firefox_options = Options()
	firefox_options.headless = True
	geckodriver_path = '/usr/local/bin/geckodriver'


def start_driver(chosen_driver = chosen_driver):
	if chosen_driver == 'chrome':
		driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
	elif chosen_driver == 'firefox':
		driver = webdriver.Firefox(options = options, executable_path = '/usr/local/bin/geckodriver')
	else:
		driver = None
	return (driver)


  



max_errors = 5

def delay():
	return (1)

def scrape_one(page, max_errors = max_errors):
	for _ in range(max_errors):
		response = requests.get(page)
		if response.status_code ==429:
			raise exceptions.GreedyError
		if response.status_code ==200:
			return (response.text)
	else:
		raise Exception("too many errors; last status"+ str(response.status_code) + '; text: '+response.text )

	

def scrape_many(pages,delay=delay):
	session = FuturesSession()
	requests = []
	for page in pages:
		requests.append(session.get(page))
		time.sleep(delay)
	return (requests)


def find_and_parse_many_pages(base_url, page_list, parser, loud=True, kw_dic={}):
	'''
	returns a list of lists of relative links

	first argument is a base url added in case these are relative links
	second argument is an iterable of page links
	third argument is a parser function
	that accepts raw html as a string.
	an optional keyword dictionary 
	is unpacked and passed to the parser.
	'''
	full_urls = [base_url + page for page in page_list]
	requests = scrape_many(full_urls)
	result_output = []
	total_number = len(requests)
	for (j,request) in enumerate(requests):
		if loud:
			print ('working on request',j+1,'of',total_number)
		response = request.result()
		if response.status_code == 429:
			headers = response.headers
			if 'Retry-After' in headers:
				print ('Retry after',headers['Retry-After'])
				time.sleep(float(headers['Retry-After'])+.5)
			else:
				print ('full headers: ')
				print (response.headers)
				print ()
				print ('returned body: ')
				print (response.text)
				print ()
				waiting_time =input('Wait how much longer? ')
				time.sleep(float(waiting_time))
			continue
		elif response.status_code !=200:
			logtext = 'find and parse many pages call failed with status code '
			logtext += str(response.status_code)
			logtext += ' ; page dump: '
			logtext += response.text
			log(logtext)
			continue
		response_text = response.text
		these_pages = parser(response_text, **kw_dic)
		result_output.append(these_pages)
	return (result_output)