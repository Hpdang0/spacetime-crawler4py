import re
from urllib.parse import urlparse

import bs4
import requests
import re

_LEGAL_DOMAINS = r'.ics.uci.edu/|.cs.uci.edu/|.informatics.uci.edu/|.stat.uci.edu/|/today.uci.edu/department/information_computer_sciences/'
LEGAL_DOMAINS = re.compile(_LEGAL_DOMAINS)

_TRUNCATE = r'[#].*'
TRUNCATE = re.compile(_TRUNCATE)

NO_CRAWL_REL = re.compile(r'nofollow|ugc|sponsored')


def scraper(url, resp):
    if str(resp.status).startswith('4') or resp.error:
        return []

    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    soup = bs4.BeautifulSoup(resp.raw_response.content, 'html.parser')
    url_parsed = urlparse(url)
    url_base_compiled = url_parsed[0] + '://' + url_parsed[1]
    
    all_links = [link.get('href') for link in soup.find_all(is_tag_crawlable)]
    all_links = list(filter(lambda link: append_path(url_base_compiled, link), all_links))
    all_links = map(truncate_fragment, all_links)

    legal_links = set(filter(is_legal_and_valid, all_links))

    # Debugging purposes
    # print(">> Found all links:\n>> " + "\n>> ".join(all_links))
    # print(">> Returning legal links:\n>> " + "\n>> ".join(legal_links))
    
    return legal_links

def is_tag_crawlable(tag):
    if tag.name != 'a':
        return False

    if not tag.has_attr('rel'):
        return True

    for attr in tag['rel']:
        if NO_CRAWL_REL.search(attr) is not None:
            return False
        return True

def append_path(url, path:str):
    # print(url, path)
    if path is None or not path.startswith('/'):
        return path
    
    return url+path

def is_legal_and_valid(url):
    # Checks to see if URL is within our intended scope
    if LEGAL_DOMAINS.search(url) is not None:
        return is_valid(url)
    return False

def truncate_fragment(url):
    # Completely removes the fragment portion of the URL
    return TRUNCATE.sub('', url)

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
            + r"|ppsx)$", parsed.path.lower())    

    except TypeError:
        print ("TypeError for ", parsed)
        raise