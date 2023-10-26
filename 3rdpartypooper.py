import time
import requests
import argparse
import sys
import random
import string
import os
from dns_resolver import resolve, resolve_ipv4, resolve_ipv6
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from requests_html import HTMLSession
from html import unescape
from html_similarity import style_similarity, structural_similarity, similarity
from colorama import Fore, Style

# load the source file, easier to maintain if in a separate file
sources_file = "./sources.txt"
sources = []

if os.path.exists(sources_file):
	with open(sources_file,"r") as s:
		for source in s:
			sources.append(source.rstrip())

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-k","--keyword", type=str, help="Domain keyword to look for in 3rd parties.")
args = parser.parse_args()

results = []

# require keyword
if args.keyword == None:
	print(f"{Fore.RED}[-] No keyword provided...{Style.RESET_ALL}")
	sys.exit(0)

def get_https(subdom, redirect):
	URL = "https://{}".format(subdom)
	headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36","Accept-Encoding": None}
	try:
		r = requests.get(URL, headers=headers, allow_redirects=redirect)
		return r
	except:
		print(f"{Fore.RED}[!] {URL} not accessible.{Style.RESET_ALL}")
		return None
		
# Check 4
def compare_location_headers(response, random_response, subdom, random_subdom):
	if 'Location' in response.headers.keys() and 'Location' in random_response.headers.keys():
		if response.headers['Location'].startswith(f"https://{subdom}") or response.headers['Location'].startswith(f"http://{subdom}"):
			if random_response.headers['Location'].startswith(f"https://{random_subdom}") or random_response.headers['Location'].startswith(f"http://{random_subdom}"):
				return True
			else:
				return False
	return True

# Check 5
def compare_content_length(response, subdom):
	random_subdomain1 = get_random_subdom(subdom)
	random_subdomain2 = get_random_subdom(subdom)
	random_subdomain3 = get_random_subdom(subdom)
	random_response1 = get_https(random_subdomain1,False)
	random_response2 = get_https(random_subdomain2,False)
	random_response3 = get_https(random_subdomain3,False)
	if random_response1 == None or random_response2 == None or random_response3 == None:
		return True
	if "Content-Length" in response.headers.keys() and "Content-Length" in random_response1.headers.keys() and "Content-Length" in random_response2.headers.keys() and "Content-Length" in random_response3.headers.keys():
		if random_response1.headers["Content-Length"] == random_response2.headers["Content-Length"] == random_response1.headers["Content-Length"] != response.headers["Content-Length"]:
			return False
	return True

# Check 6
def compare_with_redirects(subdom):
	random_subdomain1 = get_random_subdom(subdom)
	random_subdomain2 = get_random_subdom(subdom)
	
	response = get_https(subdom,True)
	random_response1 = get_https(random_subdomain1,True)
	random_response2 = get_https(random_subdomain2,True)
	
	html = unescape(response.text)
	html_random1 = unescape(random_response1.text)
	html_random2 = unescape(random_response2.text)
	
	try:
		similarity_random_htmls = similarity(html_random1,html_random2)
		#print("Redirected - Similarity between randoms " + str(similarity_random_htmls))
		similarity_htmls = similarity(html,html_random1)
		#print("Redirected - Similarity between tested site and random " + str(similarity_htmls))
		if similarity_htmls + 0.05 > similarity_random_htmls:
			return True
		else:
			return False
	except:
		print("Error... skipping compare_with_redirects")

# Check 7
def run_page_dynamically(subdom):
	URL = "https://{}".format(subdom)
	session = HTMLSession()
	resp = session.get(URL)
	resp.html.render(sleep=2)
	return resp.html.html

# Check 7
def compare_dynamically(subdom):
	random_subdomain1 = get_random_subdom(subdom)
	random_subdomain2 = get_random_subdom(subdom)

	html = run_page_dynamically(subdom)
	random_html1 = run_page_dynamically(random_subdomain1)
	random_html2 = run_page_dynamically(random_subdomain2)
	
	try:
		similarity_random_htmls = similarity(random_html1,random_html2)
		#print("Dynamically - Similarity between randoms " + str(similarity_random_htmls))
		similarity_htmls = similarity(html,random_html1)
		#print("Dynamically - Similarity between tested site and random " + str(similarity_htmls))
		if similarity_htmls + 0.05 > similarity_random_htmls:
			return True
		else:
			return False
	except:
		print("Error... skipping compare_dynamically")

def get_random_subdom(subdom):
	random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=len(subdom.split(".")[0]))).lower()
	return random_string + subdom[len(random_string):]

# Check 8
def get_html_selenium(driver,subdom):
	driver.get("https://{}".format(subdom))
	time.sleep(2)
	return driver.page_source
	
# Check 8
def compare_selenium(subdom):
	options = uc.ChromeOptions()
	options.add_argument("--disable-renderer-backgrounding")
	options.add_argument("--disable-backgrounding-occluded-windows")
	driver = uc.Chrome(options=options,headless=True,use_subprocess=True)
	driver.set_page_load_timeout(15)
	driver.set_script_timeout(15)
	
	similarity_random_htmls = 0
	
	while similarity_random_htmls < 0.9:
		try:
			html = get_html_selenium(driver, subdom)
			random_subdomain1 = get_random_subdom(subdom)
			random_subdomain2 = get_random_subdom(subdom)
			random_html1 = get_html_selenium(driver, random_subdomain1)
			random_html2 = get_html_selenium(driver, random_subdomain2)
			similarity_random_htmls = similarity(random_html1,random_html2)
		except TimeoutException:
			print(f"{Fore.RED}[-] Timeout error for {subdom} {Style.RESET_ALL}")
			driver.quit()
			return True		
	driver.quit()
		
	try:
		#print("Selenium - Similarity between randoms " + str(similarity_random_htmls))
		similarity_htmls = similarity(html,random_html1)
		#print("Selenium - Similarity between tested site and random " + str(similarity_htmls))
		if similarity_htmls + 0.05 > similarity_random_htmls:
			return True
		else:
			return False
	except:
		print("Error... skipping compare_selenium")

# This is were HTTPS accessibility checks are done (Phase 2-8) 
def compare_https(subdom,random_subdom):
	response = get_https(subdom,False)
	random_response = get_https(random_subdom,False)
	# Check 2
	if response == None and random_response == None:
		print(f"{Fore.BLUE}[*] None of the subdomains were accessible: https://{subdom}, https://{random_subdom}{Style.RESET_ALL}")
		return True
	elif response != None and random_response == None:
		print(f"{Fore.BLUE}[*] https://{subdom} was accessible and a random subdomain wasn't.{Style.RESET_ALL}")
		return False
	# Check 3
	elif response.status_code == 404 and random_response.status_code == 404:
		print(f"{Fore.BLUE}[*] https://{subdom} and https://{random_subdom} returned 404.{Style.RESET_ALL}")
		return True
	elif random_response != None and response != None and response.status_code != random_response.status_code:
		print(f"{Fore.BLUE}[*] Different status codes between https://{subdom} and https://{random_subdom}.{Style.RESET_ALL}")
		return False
	# Check 4
	elif compare_location_headers(response, random_response, subdom, random_subdom) == False:
		print(f"{Fore.BLUE}[*] Different location headers between https://{subdom} and https://{random_subdom}.{Style.RESET_ALL}")
		return False
	# Check 5
	elif compare_content_length(response, subdom) == False:
		print(f"{Fore.BLUE}[*] Different content-length generated between https://{subdom} and a similar length random subdomains.{Style.RESET_ALL}")
		return False
	# Check 6
	elif compare_with_redirects(subdom) == False:
		print(f"{Fore.BLUE}[*] Different content returned upon redirections for https://{subdom} and a similar length random subdomains.{Style.RESET_ALL}")
		return False
	# Check 7
	elif compare_dynamically(subdom) == False:
		print(f"{Fore.BLUE}[*] Different dynamic content generated between https://{subdom} and random subdomains.{Style.RESET_ALL}")
		return False
	# Check 8
	elif compare_selenium(subdom) == False:
		print(f"{Fore.BLUE}[*] Different content after opening https://{subdom} and random subdomains in browser.{Style.RESET_ALL}")
		return False	
	else:
		print(f"{Fore.BLUE}[*] No differences spotted between https://{subdom} and https://{random_subdom}, could not determine subomains' existence.{Style.RESET_ALL}")
		return True

# this is where DNS based checks are performed (Phase 1)
def company_registered(source, keyword):
	subdomain = source.format(keyword)
	resolved = resolve_ipv4(subdomain)
	if len(resolved) > 0:
		random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32)).lower()
		random_subdomain = source.format(random_string)
		random_resolved = resolve_ipv4(subdomain)
		if len(random_resolved) > 0:
			if not compare_https(subdomain,random_subdomain):
				print(f"{Fore.CYAN}[+] {subdomain} is a valid company tenancy. (https://{subdomain} gives a different result from random subdomain){Style.RESET_ALL}")
				return True
			else:
				return False
		else:
			print(f"{Fore.CYAN}[+] {subdomain} is a valid company tenancy. ({subdomain} resolves but a random subdomain doesn't){Style.RESET_ALL}")
			return True
		
	else:
		print(f"{Fore.RED}[-] {subdomain} did not resolve...{Style.RESET_ALL}")
		return False
		

for source in sources:
	try:
		source = "{}." + source
		if company_registered(source,args.keyword):
			results.append("https://" + source.format(args.keyword))
	except:
		print(f"{Fore.RED}[-] Error... skipping {source}{Style.RESET_ALL}")
		
# write out the results
if len(results) > 0:
	print(f"{Fore.GREEN}[+] The following instances were found:{Style.RESET_ALL}")
	for result in results:
		print(f"{Fore.GREEN}{result}{Style.RESET_ALL}")
else:
	print(f"{Fore.RED}[-] No instances were found...{Style.RESET_ALL}")
