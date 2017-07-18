import logging

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class BrowserScraper():


    def __init__(self, profile=None):
        '''
        Scraper using selenium

        Args:
            profile: string, path to firefox profile, e.g. $HOME/.mozilla/firefox/6h98gbaj.default'    
        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        self.display = Display(visible=0, size=(800, 600))
        self.display.start()
        caps = DesiredCapabilities.FIREFOX
        caps["marionette"] = True
        if profile:
            self.browser = webdriver.Firefox(capabilities=caps, firefox_profile=webdriver.FirefoxProfile(profile))
        else:
            self.browser = webdriver.Firefox(capabilities=caps)

    def get(self, url):
        '''
        Gets page using headless firefox
        
        Args:
            url: string

        Returns:
            string of HTML
        '''
        self.browser.get(url)
        elem = self.browser.find_element_by_xpath("//*")
        return elem.get_attribute("outerHTML")


if __name__ == "__main__":
    pass