from scraper import scrape_one
from bs4 import BeautifulSoup
# import numpy as np
from number_parser import parse_number

base_url = 'https://www.ratebeer.com'
regions_page = '/brewery-directory.asp'
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


def find_ratebeer_regions(regions_page = regions_page):
	'''
	returns a list of relative links to region pages

	optional argument specifying where to look that 
	usually shouldn't need specification
	'''
	response_text = scrape_one(base_url+regions_page)
	response_soup = BeautifulSoup(response_text,'html.parser')
	parent_div = response_soup.find('div',id='default')
	anchors = parent_div.find_all('a')
	links = [a['href'] for a in anchors]
	return (links)

def find_ratebeer_breweries(region_page, active_only = False):
	'''
	returns a list of relative links to brewery pages

	optional argument specifying whether to look only at active breweries
	default false
	'''
	response_text = scrape_one(base_url+region_page)
	response_soup = BeautifulSoup(response_text,'html.parser')
	tables = response_soup.find_all(id='brewerTable')
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

def find_ratebeer_beers(brewery_page):
	'''
	returns a list of relative links to beer pages
	'''
	response_text = scrape_one(base_url+brewery_page)
	response_soup = BeautifulSoup(response_text,'html.parser')
	tbody = response_soup.find('tbody')
	table_rows = tbody.find_all('tr')
	anchors = [row.td.strong.a for row in table_rows]
	links = [a['href'] for a in anchors]
	return (links)


def parse_ratebeer_beer(beer_soup):
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
	# findable_div = beer_soup.find(class_='sc-hrWEMg')
	wrapping_div = beer_soup.find(class_='p-4')
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