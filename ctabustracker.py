"""
ctabustracker.py

This is a Python module that offers access to all of the data available
in the CTA Bus Tracker API.  This is based on the CTA Bus Tracker API
documentation v1.0/rev.2009-12-14, available at:
http://www.transitchicago.com/asset.aspx?AssetId=2917

The CTA bus tracker API returns data in XML, and this module converts
the information to more sane data structures.

Note that this does not currently cover L trains, as they do not exist in the 
API at the time of creation (Jul 2010).  Rumor has it that it's on its way soon.
"""

__author__ = "Chris Swingler"
__email__ = "chris@chrisswingler.com"
__status__ = "Development"

import time
import urllib2
import xml.etree.ElementTree as etree

# Logger setup
import logging
logging.basicConfig(level = logging.DEBUG)
log = logging.getLogger('ctabustracker')

# Utility functions. May want to make these public?
def convert_time(timestring):
    """
    Converts a CTA time stamp from XML into a
    time_struct
    """
    try:
        return time.strptime(timestring, "%Y%m%d %H:%M:%S")
    except ValueError:
        # For some reason, the API supports seconds in some places,
        # and not elsewhere.
        return time.strptime(timestring, "%Y%m%d %H:%M")



class ctabustracker:
    """
    Creates an object that can be used to query Bus Tracker information
    """
    # Private variables:

    # API key
    __api_key = None 

    __api_url = "http://www.ctabustracker.com/bustime/api/v1/"

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

    def __make_etree(self, xml):
        """
        Returns an elementtree object from xml.
        """
        return etree.fromstring(xml)

    def __convert_time(self, timestring):
        """
        Converts a CTA time stamp from XML into a
        time_struct
        """
        try:
            return time.strptime(timestring, "%Y%m%d %H:%M:%S")
        except ValueError:
            # For some reason, the API supports seconds in some places,
            # and not elsewhere.
            return time.strptime(timestring, "%Y%m%d %H:%M")


    def __get_api_response(self, command, param_dict=None):
        """
        Returns the response from the API.
        command: str, command from the base URL.
        param_dict: dict, keys and results to be submitted as
        HTTP parameters
        """

        url = self.__api_url + command + "?key=" + self.__api_key
        if(param_dict != None):
            for dkey in param_dict:
                url += "&" + urllib2.quote(dkey) + "=" + urllib2.quote(param_dict[dkey])

        log.debug("Generated URL: "+ url)

        return self.__get_http_response(url)

    def gettime(self):
        """
        Returns the time (as a time object) 
        as according to the BusTracker system.
        """

        local_time = time.localtime()

        url = self.__api_url + "gettime?key=" + self.__api_key
        response = self.__get_http_response(url)

        tree = etree.fromstring(response)
        timestring = tree.findtext("tm")
        cta_time = time.strptime(timestring, "%Y%m%d %H:%M:%S")

        log.debug("TIME CALLED:")
        log.debug("Local System time: " + time.strftime("%Y%m%d %H:%M:%S", local_time))
        log.debug("CTA time: " + time.strftime("%Y%m%d %H:%M:%S", cta_time))

        time_diff = abs(time.mktime(local_time) - time.mktime(cta_time))
        log.debug("Time difference: " + str(time_diff))
        if ( time_diff > 5 ):
            log.warn("Time difference between CTA and local system clock is greater than 5 seconds!") 

        return cta_time

    def getvehicles_vid(self, *vehicleids):
        """
        Retrieves bus locations for the given bus IDs.  vehicle_ids
        can either be a single integer (for one bus) or a list of up to
        10 elements.
        """

        if (len(vehicleids) > 10 or len(vehicleids) < 0):
            raise ImproperNumberOfItemsException(len(vehicleids))

        val = str()
        for vid in vehicleids:
            val = val + str(vid) + ","
        val = val.rstrip(",")

        querydict = {"vid": val}

        api_result = self.__get_api_response("getvehicles",querydict)

        debug_start_time = time.time()
        root = etree.fromstring(api_result)
        vehicles_xml = root.findall('vehicle')

        vehicles = list()
        for vehicle in vehicles_xml:
            # Yank the delay flag out
            try:
                vehicle.find('dly').text
            except AttributeError:
                delayed = False
            else:
                delayed = True
            # Create an empty vehicle object
            v_obj = Vehicle(vehicle_id = vehicle.find('vid').text, \
                            timestamp = vehicle.find('tmstmp').text, \
                            lat = vehicle.find('lat').text, \
                            long = vehicle.find('lon').text, \
                            heading = vehicle.find('hdg').text, \
                            pattern_id = vehicle.find('pid').text, \
                            pattern_distance = vehicle.find('pdist').text, \
                            route = vehicle.find('rt').text, \
                            dest = vehicle.find('des').text, \
                            delayed = delayed)


#             v_obj = Vehicle()
#             v_obj.vehicle_id = str(vehicle.find('vid').text)
#             v_obj.timestamp = self.__convert_time(vehicle.find('tmstmp').text)
#             v_obj.lat = float(vehicle.find('lat').text)
#             v_obj.long = float(vehicle.find('lon').text)
#             v_obj.heading = int(vehicle.find('hdg').text)
#             v_obj.pattern_id = int(vehicle.find('pid').text)
#             v_obj.pattern_distance = int(vehicle.find('pdist').text)
#             v_obj.route = str(vehicle.find('rt').text)
#             v_obj.dest = str(vehicle.find('des').text)
            # This element will only exist if the bus is delayed
#            try:
#                vehicle.find('dly').text
#            except AttributeError:
#                 v_obj.delayed = False
#             else:
#                 v_obj.delayed = True
#             # Append it to the vehicles list
            vehicles.append(v_obj)

        log.debug("XML Processing time for getvehicles_vid(): " + str(time.time() - debug_start_time))
        return vehicles

    def getvehicles_rt(self, *routes):
        """
        Retrieves the vehicles available on the specified routes.
        Up to 10 routes can be specified.
        """

        if (len(routes) > 10 or len(routes) < 1):
            raise ImproperNumberOfItemsException(len(routes))

        val = str()
        for route in routes:
            val = val + str(route) + ","
        val = val.rstrip(",")

        querydict = {"rt":val}

        api_result = self.__get_api_response("getvehicles",querydict)

        debug_start_time = time.time()
        root = etree.fromstring(api_result)
        vehicles_xml = root.findall('vehicle')

        vehicles = list()
        for vehicle in vehicles_xml:
            # Create an empty vehicle object
            v_obj = Vehicle()
            v_obj.vehicle_id = str(vehicle.find('vid').text)
            # XXX to fix: this only is granular to minutes

            v_obj.timestamp = self.__convert_time(vehicle.find('tmstmp').text)
            v_obj.lat = float(vehicle.find('lat').text)
            v_obj.long = float(vehicle.find('lon').text)
            v_obj.heading = int(vehicle.find('hdg').text)
            v_obj.pattern_id = int(vehicle.find('pid').text)
            v_obj.pattern_distance = int(vehicle.find('pdist').text)
            v_obj.route = str(vehicle.find('rt').text)
            v_obj.dest = str(vehicle.find('des').text)
            # This element will only exist if the bus is delayed
            try:
                vehicle.find('dly').text
            except AttributeError:
                v_obj.delayed = False
            else:
                v_obj.delayed = True
            # Append it to the vehicles list
            vehicles.append(v_obj)

        log.debug("XML Processing time for getvehicles_rt(): " + str(time.time() - debug_start_time))
        return vehicles

    def getroutes(self):
        """
        Returns a dict of available routes
        """
        api_result = self.__get_api_response("getroutes")

        root = etree.fromstring(api_result)
        routes_xml = root.findall('route')
        routes = dict()

        for route in routes_xml:
            routes[str(route.find('rt').text)] = str(route.find('rtnm').text)

        return routes

    def getroute_directions(self, route):
        """
        Returns a list of directions a given route can go
        """
        route = str(route)

        querydict = {"rt": route}
        api_result = self.__get_api_response("getdirections",querydict)

        root = etree.fromstring(api_result)

        directions = list()
        dirs_xml = root.findall('dir')

        for dir in dirs_xml:
            directions.append(dir.text)

        return directions

    def getroute_stops(self, route, direction):
        """
        Returns a list of Stop objects on a given route
        direction must be a string specifing the direction of the bus.

        The returned list is unordered. Ordering is accomplished
        by constructing a pattern.
        """
        route = str(route)

        querydict = {"rt": route, "dir": direction}
        api_result = self.__get_api_response("getstops", querydict)

        root = etree.fromstring(api_result)

        stops = list()
        stops_xml = root.findall('stop')

        for stop in stops_xml:
           s_obj = Stop(stop_id = stop.find('stpid').text, \
                        stop_name = stop.find('stpnm').text,
                        lat = stop.find('lat').text,
                        long = stop.find('lon').text)
           stops.append(s_obj)
        return stops

    def getpatterns_pid(self, *patternids):
        """
        Returns patterns given a list of up to 10 pattern ids
        """

        if (len(patternids) > 10):
            raise ImproperNumberOfItemsException(len(patternids))

            

        pid_query_string = str()
        for pid in patternids:
            pid_query_string = pid_query_string + str(pid) + ", "
        pid_query_string.rstrip(",")

        querydict = {"stpid": pid_query_string}

        api_result = self.__get_api_response("getpatterns", querydict)

        pass

    def getpatterns_rt(self, route):
        """
        Returns a single pattern given a route
        """
        pass




        
# BusTrackerObjects

class Vehicle:
    """
    An object that holds information about a vehicle.
    """

    # Vehicle ID (Bus number for busses)
    """
    Vehicle ID (Bus number for buses)
    """
    vehicle_id = int()

    # Time information was obtained
    timestamp = None

    # Latitude position of the vehicle
    lat = float()

    # Longitude position of the vehicle
    long = float()

    # Direction vehicle is heading
    # TODO: Define constants to these (though these are
    # degree-based, with 0 being north)
    heading = int()

    # Pattern ID of trip (see getpatterns)
    pattern_id = int()

    # Linear distance in feet that the vehicle has travelled in this pattern.
    pattern_distance = int()

    # Route ()
    route = str()

    # Destination
    dest = str()

    # Delayed?
    delayed = bool()

    # FOR FUTURE USE:
    pattern = None # Stores a Pattern object for this bus. 

    def __init__(self, vehicle_id, timestamp, lat, \
                 long, heading, pattern_id, \
                 pattern_distance, dest, route, delayed = False):
        """
        Constructor
        """
        self.vehicle_id = int(vehicle_id)
        self.timestamp = convert_time(timestamp)
        self.lat = float(lat)
        self.long = float(long)
        self.heading = int(heading)
        self.pattern_id = int(pattern_id)
        self.pattern_distance = int(pattern_distance)
        self.route = str(route)
        self.delayed = bool(delayed)

    def __str__(self):
        """
        Thrilling string creation stuff! Just dumps the information out in a readable manner.
        """
        # TODO: This is not pythonic, or even readable!
        return "Bus number: " + str(self.vehicle_id) + \
        "\nTime of update: " + str(time.asctime(self.timestamp)) + \
        "\nLatitude: " + str(self.lat) + \
        "\nLongitude: " + str(self.long) + \
        "\nHeading: " + str(self.heading) + \
        "\nPattern_ID: " + str(self.pattern_id) + \
        "\nDistance traveled: " + str(self.pattern_distance) + \
        "\nRoute: "+ str(self.route) + \
        "\nDestination: "+ str(self.dest) + \
        "\nDelayed?: "+ str(self.delayed) 

class Stop:
    """
    Holds information about a stop
    """

    # Stop ID number
    stop_id = int()

    # Stop name
    stop_name = str()

    # Latitude
    lat = float()

    # Longitude
    long = float()

    def __init__(self, stop_id = None, stop_name = None, lat = None, long = None):
        """
        Creates a Route object
        """
        try:
            self.stop_id = int(stop_id)
            self.stop_name = str(stop_name)
            self.lat = str(lat)
            self.long = str(long)
        except TypeError:
            # Expected - probably was passed in nothing.
            pass

        return

    def __str__(self):
        """
        String representation of a Stop object
        """

        return "Stop #: " + str(self.stop_id) + " | " + \
                "Stop name: " + str(self.stop_name) + " | " + \
                "Latitude: " + str(self.lat) + " | " + \
                "Longitude: " + str(self.long)

class Pattern:
    """
    A Pattern is a series of Points and related metadata.
    """
    pass


class Point:
    """
    A point is a geographic coordinate, direction, and
    related metadata. Many Points make up a Pattern.
    """

    # Position of this point relative to other points in a pattern
    seq = int()

    # ptype - W = Waypoint, S = stop.
    ptype = str()

    # stop_id - stop ID number
    stop_id = int()

    # stop_name - stop name
    stop_name = str()

    # pattern_distance - distance from start in pattern
    pattern_distance = float()

    # lat - Latitude
    lat = float()

    # long - longitude
    long = float()

    def __init__(seq = None, ptype = None, stop_id = None, stop_name = None, pattern_distance = None, lat = None, long = None):
        """
        Constructor.  Any of the given parameters can be empty.
        """
        # TODO - Test this! I'm not sure if this will actually populate everything
        # if something turns out to be None.
        try:
            self.seq = int(seq)
            self.ptype = str(seq)
            self.stop_id = str(stop_id)
            self.stop_name = str(stop_name)
            self.pattern_distance = float(pattern_distance)
            self.lat = float(lat)
            self.long = float(long)
        except TypeError:
            passs

    pass

# EXCEPTION DEFINITIONS

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class ImproperNumberOfItemsException(Error):
    """
    Exception raised for lists exceeding preset limits.
    """

    def __init__(self, numOfItems):
        self.itemListLen = numOfItems

    def __str__(self):
        return "Improper Number of Items: 0 < items <= 10 are allowed. " + self.itemListLen + " specified."

class InvalidParamtersException(Error):
    """
    Exception raised if the parameters given to a function are incorrect.
    
    Attributes:
        msg - Message to return.
    """

    def __init__ (self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
