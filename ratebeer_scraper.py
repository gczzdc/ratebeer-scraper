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


delay = 1.2

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
	arguments
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
		output = action_function(*arguments)
		time.sleep(delay)
		with open(file_name, 'wb') as f:
			pickle.dump(output,f)
	else:
		with open(file_name, 'rb') as f:
			output = pickle.load(f)
	return (output)


def generate_all(loud=True):
	"""
	get all beer files for ratebeer, skipping locally cached ones

	stores them algorithmically as pickles
	"""
	regions = check_local(regions_page_file, find_regions, [])
	region_length = len(regions)
	all_breweries = []
	for (j,region) in enumerate(regions):
		breweries_file = 'breweries/'+clean_address_for_filename(region)+'.pickle'
		if loud:
			print ('working on region ',j, 'of', region_length)
		breweries = check_local(breweries_file, find_breweries, [region,])
		all_breweries.extend(breweries)
	brewery_length = len(all_breweries)
	all_beers = []
	for j,brewery in enumerate(all_breweries):
		beers_file = 'brewers/'+clean_address_for_filename(brewery)+'.pickle'
		if loud:
			print ('working on brewery ',j, 'of', brewery_length)
		beers = check_local(beers_file, find_beers, [brewery,])
		all_beers.extend(beers)
	beer_length = len(all_beers)
	for (j,beer) in enumerate(all_beers):
		beer_file = 'beers/'+clean_address_for_filename(beer)+'.pickle'
		if loud:
			print ('working on beer ',j, 'of', beer_length)
		beer_data = check_local(beer_file, scrape_and_parse_beer, beer)		


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


def find_async_breweries(region_pages, active_only=False):
	'''
	returns a list of lists of relative links to brewery pages

	optional argument specifying whether to look only at active breweries
	default false
	'''
	kw_dic = {'active_only':active_only}
	return (scraper.find_and_parse_many_pages(
		base_url = base_url, 
		page_list =region_pages, 
		parser =parse_region_page,
		loud = True, 
		kw_dic=kw_dic))
	
def find_async_beers(brewery_pages):
	'''
	returns a list of lists of relative links to beer pages
	'''
	return (scraper.find_and_parse_many_pages(
		base_url=base_url,
		page_list = brewery_pages,
		parser = parse_brewery_page,
		loud = True))

def find_beers(brewery_page):
	'''
	returns a list of relative links to beer pages
	'''
	response_html = scraper.scrape_one(base_url+brewery_page)
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

def scrape_and_parse_beer(beer_page):
	'''
	attempts to scrape and parse a beer page

	this needs to use selenium to handle redirects
	empirically this means that we should wait .3 seconds
	before accessing page source to parse.
	'''
	driver = scraper.scrape_one_js(base_url + beer_page)
	beer_info = {}
	for j in range(scraper.max_errors):
		time.sleep(scraper.js_sleep)
		beer_html = driver.page_source
		try:
			beer_info = parse_beer(beer_html)
			break
		except exceptions.ParseError:
			pass
	else:
		log('Failed to parse beer page '+beer_page)
	driver.close()
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
	info_and_text_divs= wrapping_div.find_all('div',recursive=False)
	info_div = info_and_text_divs[0]
	text_div = info_and_text_divs[1]
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
	return(beer_info)



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