from threading import Thread

from utils.download import download
from utils import get_logger
from scraper import scraper, is_valid
from bs4 import BeautifulSoup
from tinydb import TinyDB, Query
import re

from tokenizer import Tokenizer

import time
class Data():
    def __init__(self, name = 'db.json'):
        self.name = name
        self.data = TinyDB(name)
        self.num_urls = 0
        self.token_count = 0

    def insert(self, contents): # contents should be a dict {url:[tokens]}
        self.data.insert(contents)
        self.num_urls += 1
        self.token_count += len(list(contents.values())[0])

class Worker(Thread):
    class db_cache():
        def __init__(self, size = 5):
            self._max_size = size
            self._queue = list()
        
        def append(self, element):
            if len(self._queue) >= self._max_size:
                self._queue.pop(0)
            self._queue.append(element)

        def __str__(self):
            return str(self._queue)

        def __repr__(self):
            return "Cache({})".format(self._max_size)

        def __iter__(self):
            self.current = -1
            return self

        def __next__(self):
            self.current += 1
            if self.current < len(self._queue):
                return self._queue[self.current]
            raise StopIteration


    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.token = Tokenizer()
        self.tiny = Data()
        super().__init__(daemon=True)
        self.cache = self.db_cache()
        self.low_value_threshold = 20
        
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            # If URL that was added into frontier was invalid, do not download it
            if not is_valid(tbd_url):
                self.frontier.mark_url_complete(tbd_url)
                time.sleep(self.config.time_delay)
                continue

            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")

            # Check for any erroes from teh download
            if str(resp.status).startswith('4') or resp.error:
                self.frontier.mark_url_complete(tbd_url)
                time.sleep(self.config.time_delay)
                continue
            
            # Text Extraction
            untokenized_text = self.extract_text(resp)
            tokenized_text = self.token.Tokenize(untokenized_text)

            # Determine if indexing is worthwhile
            low_value_page = False
            if sum(tokenized_text.values()) < self.low_value_threshold:
                low_value_page = True
                self.logger.info('[SKIPPING] URL found to be of low value: {0} tokens'.format(sum(tokenized_text.values())))

            # Compare similarity to last 5 pages we crawled in
            similar = False
            for url_token_pair in self.cache:
                if self.token.Similarity(tokenized_text, url_token_pair[1]):
                    similar = True
                    self.logger.info('[SKIPPING] Similarity found between these two urls. Skipping the second url...\n{0}\n{1}'.format(url_token_pair[0], tbd_url))
                    break
            
            # Add page into self.cache
            self.cache.append((tbd_url, tokenized_text))
            
            if not similar and not low_value_page:
                # Insert into DB
                self.tiny.insert({tbd_url : tokenized_text}) # inserting the text into the tinydb
                
                # Link Extraction
                scraped_urls = scraper(tbd_url, resp)
                for scraped_url in scraped_urls:
                    self.frontier.add_url(scraped_url)
            
            # Mark as complete and sleep to be patient
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay) # <-- politeness

    def extract_text(self, resp) -> list:
        blank_list = []
        # using Beautiful Soup grabs the url from resp from the the downloaded information in the Worker Class
        soup = BeautifulSoup(resp.rawresponse.content, features= 'html.parser')
        
        # grabs content that has Id of content or tagged as content
        content_block = soup.select("#content, .content")
        
        # If the content_block got something from the beautiful soup selection "content", 
        # it would extract the text and separate into a list of words
        if content_block is not None:
            for iter in content_block:
                text = iter.get_text(strip=True,separator = ' ')
                blank_list += (text.split())
        
        # Otherwise, we would use beautiful soup's find all function to grab tags <title>, <p>, and <headers> 
        # in the document and return it as a list and same concept of extracts and outputting a list of words.
        else:
            for iter in list(soup.find_all(re.compile(r'(title|p|h[0-9])'))):
                text = iter.get_text(strip=True,separator = ' ')
                blank_list += (text.split())
        return(blank_list)
