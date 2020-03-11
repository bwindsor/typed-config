from concurrent.futures import ThreadPoolExecutor


class ThreadedRunner:
    def __init__(self, func, max_threads=1000):
        self.func = func
        self.max_threads = max_threads

    def run(self, *args):
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            results = executor.map(self.func, *args)
            return list(results)
