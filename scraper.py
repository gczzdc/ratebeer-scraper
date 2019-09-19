import requests

import os  
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options  

chrome_options = Options()  
chrome_options.add_argument("--headless")  
chrome_options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'




max_errors = 5

def scrape_one(page, max_errors = max_errors, use_selenium = False):
	recent_errors = 0
	if use_selenium:
		#note, this has no validation of html status codes (or anything else)
		driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), chrome_options=chrome_options)
		response = driver.get(page)
		return(response.page_source)
	else:
		while recent_errors < max_errors:
			response = requests.get(page)
			if response.status_code ==200:
				return (response.text)
		else:
			raise Exception("too many errors; last status"+ str(response.status_code) + '; text: '+response.text )

def scrape_many(pages):
	pass