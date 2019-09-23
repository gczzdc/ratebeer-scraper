import scraper
from bs4 import BeautifulSoup
# import numpy as np
from number_parser import parse_number
import exceptions
from error_logger import log
import time
import os
import pickle
import random
import numpy as np


# delay = 1.2

html_parser = 'html.parser'
base_url = 'https://www.ratebeer.com'
regions_page = '/brewery-directory.asp'
regions_page_file = 'regions/regions.pickle'

# web-accessible database structure for ratebeer:
#
# https://www.ratebeer.com/brewery-directory.asp
# returns a list of regions
# 
# each region eg.
# https://www.ratebeer.com/breweries/pennsylvania/38/213/
# returns a list of active and closed breweries 
# note, 38 is probably the US and 213 the subregion PA
#
# each brewery eg.
# https://www.ratebeer.com/brewers/allegheny-city-brewing/28937/
# returns a list of beers

default_delay=2.5

def check_empty(file):
	return (os.stat(file).st_size == 0)

def clean_address_for_filename(s):
	"""
	replace non-alpha-numeric with '-'

	"""
	clean_s = ''
	for character in s[1:]:
		if character.isalnum():
			clean_s += character
		else:
			clean_s += '-'
	return (clean_s)


def check_local(
	file_name,
	action_function, 
	arguments,
	delay=default_delay
	):
	'''
	checks local pickle cache and then fetches remotely

	file_name is where we look for the pickle
	if it's nonempty we assume it's a correctly formed pickle
	if it's empty we call action_function(*args)
	and write the result to our pickle file
	'''
	open (file_name,'a').close()
	if check_empty(file_name):
		local = False
		output = action_function(*arguments)
		time.sleep(delay)
		with open(file_name, 'wb') as f:
			pickle.dump(output,f)
	else:
		local=True
		with open(file_name, 'rb') as f:
			output = pickle.load(f)
	return (output, local)


def generate_all(delay = default_delay, loud=True):
	"""
	get all beer files for ratebeer, skipping locally cached ones

	stores them algorithmically as pickles
	"""
	all_regions = generate_regions(delay)
	all_breweries = generate_breweries(all_regions, delay, loud)
	all_beers = generate_beers(all_breweries, delay, loud)
	beer_data = get_beer_data(all_beers,delay,loud)
	return (beer_data)

def generate_regions(delay):
	regions,local = check_local(regions_page_file, find_regions, [],delay)
	return (regions)

def generate_breweries(regions,delay, loud = True):
	region_length = len(regions)
	all_breweries = []
	for (j,region) in enumerate(regions):
		t0 = time.time()
		breweries_file = 'breweries/'+clean_address_for_filename(region)+'.pickle'
		breweries, local = check_local(breweries_file, find_breweries, [region,],delay)
		if loud and not local:
			print ('completed region',j, 'of', region_length,'in',round(time.time()-t0,2),'seconds')
		all_breweries.extend(breweries)
	return (all_breweries)

def generate_beers(breweries, delay,loud=True):
	brewery_length = len(breweries)
	all_beers = []
	for (j,brewery) in enumerate(breweries):
		t0 = time.time()
		beers_file = 'brewers/'+clean_address_for_filename(brewery)+'.pickle'
		beers, local = check_local(beers_file, find_beers, [brewery,],delay)
		if loud and not local:
			print ('completed brewery',j, 'of', brewery_length,'in',round(time.time()-t0,2),'seconds')
		all_beers.extend(beers)
	return (all_beers)

def get_beer_data(beers, delay, loud = True):
	all_data = []
	beer_length = len(beers)
	has_ibu_and_text = 0
	total_time = 0
	non_local = 0
	driver = scraper.start_driver() #need javascript for these pages
	for (j,beer) in enumerate(beers):
		t0 = time.time()
		beer_file = 'beers/'+clean_address_for_filename(beer)+'.pickle'
		beer_data, local = check_local(beer_file, scrape_and_parse_beer, [beer,driver], delay)
		if beer_data and (not np.isnan(beer_data['ibu'])) and beer_data['text'].strip():
			has_ibu_and_text+=1
		if loud and not local:
			non_local +=1
			t1 = time.time()
			total_time+=t1-t0
			print ('completed beer',j, 'of', beer_length,'in',round(t1-t0,2),'seconds')		
			print (has_ibu_and_text,'beers with ibu and text data (ratio',round(has_ibu_and_text/(j+1) , 3),')','average time per beer',round(total_time/non_local,3))
		all_data.append(beer_data)
	driver.close()
	return (all_data)




def find_regions(regions_page = regions_page):
	'''
	returns a list of relative links to region pages

	optional argument specifying where to look that 
	usually shouldn't need specification
	'''
	response_text = scraper.scrape_one(base_url+regions_page)
	response_soup = BeautifulSoup(response_text, html_parser)
	parent_div = response_soup.find('div',id='default')
	anchors = parent_div.find_all('a')
	links = [a['href'] for a in anchors]
	return (links)

def parse_region_page(region_html,active_only=False):
	'''
	parses a raw html object that is supposed to be a region page

	optional argument specifying whether to look only at active breweries
	default false
	'''
	region_soup = BeautifulSoup(region_html, html_parser)
	tables = region_soup.find_all(id='brewerTable')
	if active_only:
		tables = tables[:1]
		# this hack probably behaves unexpectedly on a region 
		# with only closed breweries.
	brewery_pages = []
	for table in tables:
		anchors = table.find_all('a', class_=False)
		links = [a['href'] for a in anchors]
		brewery_pages.extend(links)
	return (brewery_pages)

def find_breweries(region_page, active_only = False):
	'''
	returns a list of relative links to brewery pages

	optional argument specifying whether to look only at active breweries
	default false
	'''
	response_text = scraper.scrape_one(base_url+region_page)
	return (parse_region_page(response_text,active_only))


def find_beers(brewery_page):
	'''
	returns a list of relative links to beer pages
	'''
	response_html = scraper.scrape_one(base_url+brewery_page)
	try:
		return (parse_brewery_page(response_html))
	except:
		brewery_id = brewery_page.split('/')[-2]
		response_html = scraper.scrape_one(base_url+'/Ratings/Beer/ShowBrewerBeers.asp?BrewerID='+brewery_id)
		return (parse_brewery_page(response_html))

def parse_brewery_page(brewery_html):
	'''
	returns a list of relative links to beer pages

	expects a beautiful soup of a brewery page
	'''
	brewery_soup = BeautifulSoup(brewery_html, html_parser)
	tbody = brewery_soup.find('tbody')
	table_rows = tbody.find_all('tr')
	anchors = [row.td.strong.a for row in table_rows]
	links = [a['href'] for a in anchors]
	return (links)
	

def scrape_and_parse_beer(beer_page, driver):
	'''
	attempts to scrape and parse a beer page

	this needs to use selenium to handle redirects
	empirically this means that we should wait .3 seconds
	before accessing page source to parse.
	'''
	driver.get(base_url + beer_page)
	beer_info = {}
	for j in range(scraper.max_errors):
		time.sleep(scraper.js_sleep)
		beer_html = driver.page_source
		try:
			beer_info = parse_beer(beer_html)
			break
		except exceptions.ParseError:
			pass
		except exceptions.NoFullDescription:
			try:
				driver.find_element_by_class_name('-ml-3').click()
				time.sleep(scraper.js_sleep)
				beer_info = parse_beer(driver.page_source)
			except:
				log('failed to load full text or find button for '+beer_page)
	else:
		time.sleep(scraper.js_sleep)
		beer_html = driver.page_source
		try:
			beer_info = parse_beer(beer_html)
		except exceptions.NoFullDescription as warning:
			log('failed to load full text for '+beer_page)
		except exceptions.ParseError:
			#print ('full html: ')
			#print (beer_html)
			log('ParseError for '+beer_page)
	# else:
	# 	log('Failed to parse beer page '+beer_page)
	return (beer_info)

def parse_beer(beer_html):
	'''
	saves less information than the whole webpage

	returns image location, 
	name (name is an unpleasant combination with the brewer)
	location
	style
	brewer
	ABV
	IBU
	text

	skipping the following parseable data:
	estimated calories
	rating information
	served in glass shapes
	availability
	tags
	reviews
	similar
	'''
	beer_soup = BeautifulSoup(beer_html, html_parser)
	wrapping_div = beer_soup.find(class_='p-4')
	if wrapping_div == None:
		raise exceptions.ParseError("no wrapping div")
	try:
		info_and_text_divs= wrapping_div.find_all('div',recursive=False)
		info_div = info_and_text_divs[0]
		text_div = info_and_text_divs[1]
		try:
			aka_text = text_div.span.span.text.strip() 
			if aka_text == 'Also Known As':
				alias = text_div.a.text
				return ({})
			else:
				print ('aka_text: "'+aka_text+'"')
				raise exceptions.ParseError("looks like AKA but doesn't parse")
		except:
			pass
		broken_info_div = info_div.div.find_all('div',recursive=False)
		name_and_loc_divs = broken_info_div[0].div.find_all('div',recursive=False)
		name_div = name_and_loc_divs[0]
		loc_div = name_and_loc_divs[1]
		other_info_div = broken_info_div[1]
		broken_other_divs = other_info_div.find_all('div',recursive=False)
		style_brewer_div = broken_other_divs[0]
		abv_ibu_div = broken_other_divs[1]
		style_brewer_divs = style_brewer_div.find_all('div',recursive=False)
		style_div = style_brewer_divs[0]
		brewer_div = style_brewer_divs[1]
		abv_ibu_divs = abv_ibu_div.find_all('div',recursive=False)
		abv_div = abv_ibu_divs[0]
		ibu_div = abv_ibu_divs[1]

		beer_info = {}
		beer_info['name']=name_div.text
		beer_info['location']=loc_div.text
		beer_info['brewer']=brewer_div.a.text
		beer_info['image_url'] = info_div.img['src']
		beer_info['style']=style_div.a.text

		abv_string = abv_div.div.text
		beer_info['abv']=parse_abv(abv_string)

		ibu_string = ibu_div.div.text
		beer_info['ibu']=parse_ibu(ibu_string)
		beer_info['text']=text_div.text

		if beer_info['text'] and beer_info['text'][-1]=='…':
			description_count = beer_html.count('"description"')
			if description_count==1:
				beer_info['full_text']=beer_html[beer_html.index('"description"'):].split('"')[3]
			elif description_count>1:
				raise exceptions.ParseError('too many descriptions')
			else:
				raise exceptions.NoFullDescription('not enough descriptions',beer_info['name'])
		return(beer_info)
	except (exceptions.ParseError, exceptions.NoFullDescription):
		raise
	except:
		print ('wrapping div: ')
		print (wrapping_div.prettify())
		print ()
		raise


def parse_abv(abv_string):
	'''
	parse abv to float

	abv might be a float with the '%' symbol or it might be '-' or ???

	'''
	return (parse_number(abv_string, rstrip='%'))


def parse_ibu(ibu_string):
	'''
	parse ibu to float

	ibu might be a float (probably int) or it might be '-' or ???

	'''
	return (parse_number(ibu_string))