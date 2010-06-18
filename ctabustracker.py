"""
ctabustracker.py

This is a Python module that offers access to all of the data available
in the CTA Bus Tracker API.  This is based on the CTA Bus Tracker API
documentation v1.0/rev.2009-12-14, available at:
http://www.transitchicago.com/asset.aspx?AssetId=2917

The CTA bus tracker API returns data in XML, and this module converts
the information to more sane data structures.
"""

__author__ = "Chris Swingler"
__license__ = "WTFPL"
__email__ = "chris@chrisswingler.com"
__status__ = "Development"

import time
import urllib2
import xml.etree.ElementTree as etree

class ctabustracker:
    """
    Creates an object that can be used to query Bus Tracker information
    """
    # Private variables:

    # API key
    __api_key = None 

    __api_url = "http://www.ctabustracker.com/bustime/api/v1/"

    # For future expansion - caching data
    __cache_time = 0 # Seconds


    def __init__(self, api_key, api_url = None, cache_time = None):
        """
        Initializes the API key for the CTA bus tracker.
        This module will not work without a valid key.
        If you do not have an API key, you can request one from
        http://www.transitchicago.com/developers/bustracker.aspx
        """
        self.__api_key = api_key
        if (api_url != None):
            self.__api_url = api_url
        return

    def __get_http_response(self, url):
        """
        Private method that grabs the specified URL and returns it as a 
        string.
        """
        return urllib2.urlopen(url).read()

    def gettime(self):
        """
        Returns the time (as a time object) 
        as according to the BusTracker system.
        """
        url = self.__api_url + "gettime?key=" + self.__api_key
        # Possible TODO - The above should be put in a config file.
        print url
        response = self.__get_http_response(url)

        tree = etree.fromstring(response)
        timestring = tree.findtext("tm")
        return time.strptime(timestring, "%Y%m%d %H:%M:%S")
