import logging

from nba.dates import convert_format, strtodate, subtract_datestr, today
from nba.scrapers.scraper import BasketballScraper


class WaybackScraper(BasketballScraper):


    def __init__(self, headers=None, cookies=None, cache_name=None, expire_hours=12, as_string=False):
        '''
        Scraper for waybackmachine API

        Args:
            headers: dictionary of HTTP headers
            cookies: cookie object, such as browsercookie.firefox()
            cache_name: str 'nbacomscraper'
            expire_hours: how long to cache requests
            as_string: return as raw string rather than json parsed into python data structure
        '''
        self.wburl = 'http://archive.org/wayback/available?url={}&timestamp={}'
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        BasketballScraper.__init__(self, headers=headers, cookies=cookies, cache_name=cache_name, expire_hours=expire_hours, as_string=as_string)


    def get_wayback(self, url, d=None, max_delta=None):
        '''
        Gets page from the wayback machine
        Args:
            url: of the site you want, not the wayback machine
            d: datestring, if None then get most recent one
            max_delta: int, how many days off can the last page be from the requested date
        Returns:
            content: HTML string
        '''
        content = None
        if not d:
            d = today('db')
        else:
            d = convert_format(d, 'db')
        resp = self.get_json(self.wburl.format(url, d))
        if resp:
            ts = resp['archived_snapshots']['closest']['timestamp'][:8]
            if max_delta:
                closest_url = resp['archived_snapshots']['closest']['url']
                if subtract_datestr(d, ts) <= max_delta:
                    content = self.get(resp['archived_snapshots']['closest']['url'])
                else:
                    logging.error('page is too old: {}'.format(ts))
            else:
                closest_url = resp['archived_snapshots']['closest']['url']
                return self.get(closest_url)
        else:
            logging.error('url unavailable on wayback machine')
        return content, ts


if __name__ == "__main__":
    pass