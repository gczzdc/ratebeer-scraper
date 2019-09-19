import requests
from requests_futures.sessions import FuturesSession

import os  
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

js_sleep =.5
chrome_options = Options()  
chrome_options.add_argument("--headless")  
chrome_options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
#mac-os specific

max_errors = 5

def scrape_one(page, max_errors = max_errors, use_selenium = False):
	while recent_errors < max_errors:
		response = requests.get(page)
		if response.status_code ==200:
			return (response.text)
	else:
		raise Exception("too many errors; last status"+ str(response.status_code) + '; text: '+response.text )

def scrape_one_js(page):
	#note, this has no validation of html status codes (or anything else)
	driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), options=chrome_options)
	driver.get(page)
	return(driver)
	#need to access page_source
	

def scrape_many(pages):
	session = FuturesSession()
	requests = []
	for page in pages:
		requests.append(session.get(page))
	return (requests)


def find_and_parse_many_pages(base_url, page_list, parser, kw_dic={}):
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
	for request in requests:
		response = request.result()
		if response.status_code !=200:
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