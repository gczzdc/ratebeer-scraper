import requests

max_errors = 5

def scrape_one(page, max_errors = max_errors):
	recent_errors = 0
	while recent_errors < max_errors:
		response = requests.get(page)
		if response.status_code ==200:
			return (response.text)
	else:
		raise Exception("too many errors; last status"+ str(response.status_code) + '; text: '+response.text )

def scrape_many(pages):
	pass