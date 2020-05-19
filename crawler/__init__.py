from utils import get_logger
# frontier.py
from crawler.frontier import Frontier
# worker.py
from crawler.worker import Worker

class Crawler(object):
    def __init__(self, config, restart, frontier_factory=Frontier, worker_factory=Worker):
        # starts up the config
        self.config = config
        # keeps a log of all the crawled files
        self.logger = get_logger("CRAWLER")
        # takes the config settings and resume progress if the crawler was paused
        self.frontier = frontier_factory(config, restart)
        # Establishes a list of workers (if multithreaded, should be just 1 worker in the list)
        self.workers = list()
        # Sets up worker in the crawler
        self.worker_factory = worker_factory

    def start_async(self):
        # links us the workers together
        self.workers = [
            self.worker_factory(worker_id, self.config, self.frontier)
            for worker_id in range(self.config.threads_count)]
        for worker in self.workers:
            worker.start()

    def start(self):
        # run sync up the worker
        self.start_async()
        self.join()

    def join(self):
        for worker in self.workers:
            worker.join()
