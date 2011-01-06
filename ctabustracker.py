"""
ctabustracker.py

This is a Python module that offers access to all of the data available
in the CTA Bus Tracker API.  This is based on the CTA Bus Tracker API
documentation v1.0/rev.2009-12-14, available at:
http://www.transitchicago.com/asset.aspx?AssetId=2917

The CTA bus tracker API returns data in XML, and this module converts
the information to more sane data structures.

Note that this does not currently cover L trains, as they do not exist 
in the  API at the time of creation (Jul 2010).  Rumor has it that 
it's on its way soon.
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

# Utility methods
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

    def __init__(self, api_key, api_url = None):
        """
        Initializes the API key for the CTA bus tracker.
        This module will not work without a valid key.
        If you do not have an API key, you can request one from
        http://www.transitchicago.com/developers/bustracker.aspx

        api_url is the base API url to access. If it is not
        specified, the default is used:
        http://www.ctabustracker.com/bustime/api/v1/
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

        log_http_time = time.time()
        response = self.__get_http_response(url)
        log.info("API response time: " + str(time.time() - log_http_time))
        return response


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
            # Append it to the vehicles list
            vehicles.append(v_obj)

        log.info("XML Processing time for getvehicles_vid(): " + str(time.time() - debug_start_time))
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

            vehicles.append(v_obj)

        log.info("XML Processing time for getvehicles_rt(): " + str(time.time() - debug_start_time))
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

        querydict = {"pid": pid_query_string}

        api_result = self.__get_api_response("getpatterns", querydict)

        root = etree.fromstring(api_result)

        patterns = list()
        patterns_xml = root.findall('ptr')

        for pattern in patterns_xml:
            pat_obj = Pattern(pattern_id = pattern.find('pid').text, \
                              length = pattern.find('ln').text,
                              direction = pattern.find('rtdir').text)
            for point in pattern.findall('pt'):
                if (point.find('stpid') != None):
                    stop_id = point.find('stpid').text
                else:
                    stop_id = None
                if (point.find('stpnm') != None):
                    stop_name = point.find('stpnm').text
                else:
                    stop_name = None
                if (point.find('pdist') != None):
                    pattern_distance = point.find('pdist').text
                else:
                    pattern_distance = None
                    
                point_obj = Point(seq = point.find('seq').text, \
                                  ptype = point.find('typ').text, \
                                  lat = point.find('lat').text, \
                                  long = point.find('lon').text, \
                                  stop_id = stop_id,\
                                  stop_name = stop_name,\
                                  pattern_distance = pattern_distance)
                pat_obj.append(point_obj)
            patterns.append(pat_obj)
        return patterns

    def getpatterns_rt(self, route, direction):
        """
        Returns a single pattern given a route and direction
        """
        # TODO: sanitize direction
        route = str(route)
        querydict = {"rt": route, "dir": direction}

        api_result = self.__get_api_response("getpatterns", querydict)

        root = etree.fromstring(api_result)

        patterns = list()
        patterns_xml = root.findall('ptr')

        for pattern in patterns_xml:
            pat_obj = Pattern(pattern_id = pattern.find('pid').text, \
                              length = pattern.find('ln').text,
                              direction = pattern.find('rtdir').text)
            for point in pattern.findall('pt'):
                if (point.find('stpid') != None):
                    stop_id = point.find('stpid').text
                else:
                    stop_id = None

                if (point.find('stpnm') != None):
                    stop_name = point.find('stpnm').text
                else:
                    stop_name = None

                if (point.find('pdist') != None):
                    pattern_distance = point.find('pdist').text
                else:
                    pattern_distance = None
                    
                point_obj = Point(seq = point.find('seq').text, \
                                  ptype = point.find('typ').text, \
                                  lat = point.find('lat').text, \
                                  long = point.find('lon').text, \
                                  stop_id = stop_id,\
                                  stop_name = stop_name,\
                                  pattern_distance = pattern_distance)
                pat_obj.append(point_obj)
            patterns.append(pat_obj)
        return patterns

    def getpredictions_stop(self, *stop_ids):
        """
        Returns predictions for the given stop_ids. 
        """
        if (len(stop_ids) > 10 or len(stop_ids) < 1):
            raise ImproperNumberOfItemsException(len(stop_ids))


        stop_ids_str = str()
        for stop in stop_ids:
            stop_ids_str = stop_ids_str + str(stop) + ","
        stop_ids_str = stop_ids_str.rstrip(",")


        querydict = {"stpid":stop_ids_str}
        api_result = self.__get_api_response("getpredictions", querydict)

        root = etree.fromstring(api_result)

        predictions = list()

        predictions_xml = root.findall('prd')

        predictions_list = list()
        for prediction in predictions_xml:
            pred_obj = Prediction(timestamp = prediction.find('tmstmp').text,
                                  prediction_type = prediction.find('typ').text,
                                  stop_id = prediction.find('stpid').text,
                                  stop_name = prediction.find('stpnm').text,
                                  vehicle_id = prediction.find('vid').text,
                                  distance_to_stop = prediction.find('dstp').text,
                                  route = prediction.find('rt').text,
                                  route_dir = prediction.find('rtdir').text,
                                  destination = prediction.find('des').text,
                                  predicted_eta = prediction.find('prdtm').text)
            if (prediction.find('dly') != None):
                pred_obj.delayed = True

            predictions_list.append(pred_obj)

        return predictions_list

    def getpredictions_vehicle(self, *vehicle_ids):
        """
        Returns predictions for the given vehicle_ids
        """

        if (len(vehicle_ids) > 10 or len(vehicle_ids) < 1):
            raise ImproperNumberOfItemsException(len(vehicle_ids))

        vehicle_ids_str = str()
        for vehicle_id in vehicle_ids:
            vehicle_ids_str = vehicle_ids_str + str(vehicle_id) + ","
        vehicle_ids_str = vehicle_ids_str.rstrip(",")

        querydict = {"vid":vehicle_ids_str}

        api_result = self.__get_api_response("getpredictions", querydict)
                                                   
        root = etree.fromstring(api_result)

        predictions = list()

        predictions_xml = root.findall('prd')

        predictions_list = list()
        for prediction in predictions_xml:
            pred_obj = Prediction(timestamp = prediction.find('tmstmp').text,
                                  prediction_type = prediction.find('typ').text,
                                  stop_id = prediction.find('stpid').text,
                                  stop_name = prediction.find('stpnm').text,
                                  vehicle_id = prediction.find('vid').text,
                                  distance_to_stop = prediction.find('dstp').text,
                                  route = prediction.find('rt').text,
                                  route_dir = prediction.find('rtdir').text,
                                  destination = prediction.find('des').text,
                                  predicted_eta = prediction.find('prdtm').text)
            if (prediction.find('dly') != None):
                pred_obj.delayed = True

            predictions_list.append(pred_obj)

        return predictions_list

    def geteta_from_prediction(self, prediction, use_cta_clock = True):
        """
        Returns the time (in minutes) that a vehicle is
        expected to arrive.

        Requires a Prediction object as a parameter, and
        calculates the difference agains the CTA's clock if
        use_cta_clock is True.  If it is False, it uses the  local system's
        clock.
        """

        if (use_cta_clock == True):
            timenow = self.gettime()
        else:
            timenow = time.localtime()

        return prediction.estimated_time_to_arrival(timenow)


    def getbulletins_route(self, *routes):
        """
        Gets bulletins related to routes.
        """

        if (len(routes) > 10 or len(routes) < 1):
            raise ImproperNumberOfItemsException(len(routes))

        routes_str = str()

        for route in routes:
            routes_str += str(route) + ","
        routes_str.rstrip(",")

        querydict = {'rt':routes_str}

        api_result = self.__get_api_response("getservicebulletins", querydict)

        root = etree.fromstring(api_result)

        bulletins_xml = root.findall('sb')

        bulletins_list = list()

        for bulletin in bulletins_xml:
            bulletin_obj = Service_Bulletin(name = bulletin.find('nm').text,
                                            subject = bulletin.find('sbj').text,
                                            detail = bulletin.find('dtl').text,
                                            brief = bulletin.find('brf').text,
                                            priority = bulletin.find('prty').text)
            for sb in bulletin.findall('srvc'):
                route = None
                direction = None
                stop_num = None
                stop_name = None


                if (sb.find('rt') != None):
                    route = sb.find('rt').text
                if (sb.find('rtdir') != None):
                    direction = sb.find('rtdir').text
                if (sb.find('stpid') != None):
                    stop_num = sb.find('stpid').text
                if (sb.find('stpnm') != None):
                    stop_name = sb.find('stpnm').text
                    
                bulletin_obj.append(route = route,
                                    direction = direction,
                                    stop_num = stop_num,
                                    stop_name = stop_name)

            bulletins_list.append(bulletin_obj)

        return bulletins_list

    def getbulletins_stops(self, *stopids):
        """
        Gets bulletins related to given stop ids. 
        """

        # The spec doesn't list a maximum, but I'm going to presume
        # it's still 10.
        if (len(stopids) > 10 or len(stopids) < 1):
            raise ImproperNumberOfItemsException(len(stopids))

        stopids_str = str()

        for stop in stopids:
            stopids_str += str(stop) + ","
        stopids_str.rstrip(",")

        querydict = {'rt':stopids_str}

        api_result = self.__get_api_response("getservicebulletins", querydict)

        root = etree.fromstring(api_result)

        bulletins_xml = root.findall('sb')

        bulletins_list = list()

        for bulletin in bulletins_xml:
            bulletin_obj = Service_Bulletin(name = bulletin.find('nm').text,
                                            subject = bulletin.find('sbj').text,
                                            detail = bulletin.find('dtl').text,
                                            brief = bulletin.find('brf').text,
                                            priority = bulletin.find('prty').text)
            for sb in bulletin.findall('srvc'):
                route = None
                direction = None
                stop_num = None
                stop_name = None


                if (sb.find('rt') != None):
                    route = sb.find('rt').text
                if (sb.find('rtdir') != None):
                    direction = sb.find('rtdir').text
                if (sb.find('stpid') != None):
                    stop_num = sb.find('stpid').text
                if (sb.find('stpnm') != None):
                    stop_name = sb.find('stpnm').text
                    
                bulletin_obj.append(route = route,
                                    direction = direction,
                                    stop_num = stop_num,
                                    stop_name = stop_name)

            bulletins_list.append(bulletin_obj)

        return bulletins_list
        
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

    #
    # Time information was obtained
    #
    timestamp = None

    # Latitude position of the vehicle
    lat = float()

    # Longitude position of the vehicle
    long = float()

    # Direction vehicle is heading (in degrees, 0 meaning North)
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
        return "Bus number: %s \
                \nTime of update: %s \
                \nLatitude: %s \
                \nLongitude: %s \
                \nHeading: %s \
                \nPattern_ID: %s \
                \nDistance traveled: %s \
                \nRoute: %s \
                \nDestination: %s  \
                \nDelayed?: %s " \
                % (self.vehicle_id, time.asctime(self.timestamp), self.lat, \
                   self.long, self.heading, self.pattern_id, \
                   self.pattern_distance, self.route, self.dest, self.delayed)

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

    def __init__(self, stop_id, stop_name, lat, long):
        """
        Creates a Route object
        """
        self.stop_id = int(stop_id)
        self.stop_name = str(stop_name)
        self.lat = str(lat)
        self.long = str(long)

        return

    def __str__(self):
        """
        String representation of a Stop object
        """

        return "Stop #: %s  | Stop name: %s | Latitude: %s  | Longitude: %s "\
                % (self.stop_id, self.stop_name, self.lat, self.long)

class Pattern:
    """
    A Pattern is a series of Points and related metadata.
    """
    
    # List of points (waypoints and stops)
    points = list()

    # ID of this pattern
    pattern_id = int()

    # Length of this pattern (in feet)
    length = int()

    # Direction this pattern travels in
    direction = str()

    def append(self, point):
        """
        Appends a point to this pattern
        """
        # TODO: Might want to have this sort out the points every time?
        self.points.append(point)
        return


    def __init__(self, pattern_id, length, direction, points = None):
        """
        Defines a patern. points can be a list of points, or None.
        """
        self.pattern_id = int(pattern_id)
        self.length = int(float(length)) # The API spec says this an int, but returns a float.
        self.direction = str(direction)
        if (points != None):
            for point in points:
                self.append(points)

        return

    def __str__(self):

        point_str = "Pattern ID: %s \
                \nLength: %s \
                \nDirection: %s \
                \nPoints: \n" % (self.pattern_id, self.length, self.direction)
        for point in self.points:
            point_str += "\t%s\n" % point

        return point_str


class Point(Stop):
    """
    A point is a geographic coordinate, direction, and
    related metadata. Many Points make up a Pattern.
    """

    # Position of this point relative to other points in a pattern
    seq = int()

    # ptype - Waypoint or Stop.
    ptype = str()

    # pattern_distance - distance from start in pattern
    pattern_distance = float()

    def __handle_pattern_type(self, ptype):
        if ptype == "W":
            return "Waypoint"
        elif ptype == "S":
            return "Stop"
        else:
            return ptype

    def __init__(self, seq, ptype, lat, long, stop_id = None, stop_name = None, pattern_distance = None):
        """
        Constructor for Point.
        """
        self.seq = int(seq)
        self.ptype = self.__handle_pattern_type(ptype)
        if (stop_id != None):
            self.stop_id = str(stop_id)
        else:
            self.stop_id = None
        if (stop_name != None):
            self.stop_name = str(stop_name)
        else:
            self.stop_id = None

        if (pattern_distance != None):
            self.pattern_distance = float(pattern_distance)
        else:
            self.pattern_distance = None
        self.lat = float(lat)
        self.long = float(long)
        return

class Prediction:
    """
    A prediction is an object holding when a bus is scheduled to arrive at a given stop.
    """

    # timestamp is when this prediction was taken
    timestamp = None

    # Type is "A" (arrival) or "D" (departure)
    prediction_type = str()

    # stop_id is the stop number
    stop_id = int()

    # stop_name is the stop's name
    stop_name = str()

    # vehicld_id is the vehicle's ID #
    vehicle_id = int()

    # distance_to_stop is the distance the bus needs to travel before it hits
    # this stop (in feet)
    distance_to_stop = int()

    # route is the route of this prediction
    route = str()

    # route_dir is the direction the bus is going on this route
    route_dir = str()

    # destination is the final destination of this vehicle
    destination = str()

    # predicted_eta is the time that the bus is scheduled to arrive
    predicted_eta = None

    # mins_to_arrival_at_init is the number of minutes that
    # the bus is scheduled to arrive at, at instantiation of this object
    # based on the time the prediction was generated by the remote API
    mins_to_arrival_at_init = int()

    # delayed is True if the vehicle is delayed.
    delayed = bool()

    def estimated_time_to_arrival(self, ctatime = None):
        """
        Returns the time that the bus is expected to arrive for this 
        Prediction (in minutes).

        If ctatime is unspecified, returns ETA based on the system's clock,
        otherwise, matches difference against specified time.
        """

        if (ctatime == None):
            ctatime = time.localtime()

        elif (type(ctatime) == str):
            # Presuming this is a human-readable time string as 
            # returned from the API
            ctatime == convert_time(ctatime)

        eta_seconds = time.mktime(self.predicted_eta) - time.mktime(ctatime)
        return int(eta_seconds/60)

    def __init__(self, timestamp, prediction_type, stop_id, stop_name, vehicle_id, distance_to_stop, route, route_dir, destination, predicted_eta, delayed = False):
        self.timestamp  = convert_time(timestamp)
        self.prediction_type = str(prediction_type)
        self.stop_id = int(stop_id)
        self.stop_name = str(stop_name)
        self.vehicle_id = int(vehicle_id)
        self.distance_to_stop = int(distance_to_stop)
        self.route = str(route)
        self.route_dir = str(route_dir)
        self.destination = str(destination)
        self.predicted_eta = convert_time(predicted_eta)
        self.delayed = bool(delayed)
        self.mins_to_arrival_at_init = self.estimated_time_to_arrival(self.timestamp)
        return

    def __str__(self):
        return "Prediction generated at: " + time.asctime(self.timestamp) + "\n" +\
                "Type: " + self.prediction_type + "\n" +\
                "Route: " + str(self.route) + "\n" +\
                "Direction: " + str(self.route_dir) + "\n" +\
                "Route destination: " + self.destination + "\n" +\
                "Stop number: " + str(self.stop_id) + "\n" +\
                "Stop name: " + self.stop_name + "\n" +\
                "Vehicle number:  " + str(self.vehicle_id) + "\n" +\
                "Distance away: " + str(self.distance_to_stop) + "\n" +\
                "Estimated time of arrival: " + time.asctime(self.predicted_eta) + "\n" +\
                "Minutes to arrival (at instantiation): " + str(self.mins_to_arrival_at_init)
    

class Service_Bulletin:
    """"
    Contains a service bulletin object.
    """

    # name - Unique name identifier of the service bulletin.
    # XXX The example XML doesn't have this, but the CTA schema says it's 
    # required!
    name = str()

    # subject - Bulletin subject
    subject = str()

    # Detail - Details about the bulletin.
    # Note that this is often the only field given.  Also, note that
    # you'll find HTML embedded in this response on a regular basis!
    detail = str()

    # Brief - A brief alternative to detail (these will often be the same)
    # Or empty!
    brief = str()

    # priority - The priority of this bulletin.
    priority = str()

    # affected_services - a list of SB_Service objects that are affected by
    # this bulletin.  If this list is empty, this bulletin affects
    # all CTA services.
    affected_services = list()

    def append(self, stop_name, route = None, direction = None, stop_num = None):
        """
        Appends an SB_Service object to this bulletin
        """
        log.debug("Route in append: " + str(route))
        log.debug("direction in append: " + str(direction))
        new_sb = SB_Service(route = route,
                            direction = direction,
                            stop_num = stop_num,
                            stop_name = stop_name)
        self.affected_services.append(new_sb)
        return

    def __init__(self, name, subject, detail, brief, priority, affected_services = []):
        self.name = str(name)
        self.subject = str(subject)
        self.detail = str(detail)
        self.brief = str(brief)
        self.priority = str(priority)

        return

    def __str__(self):
        return_str = "SERVICE BULLETIN:\n" +\
                "Name: " + str(self.name) + "\n" +\
                "Subject: " + str(self.subject) + "\n" +\
                "Detail: " + str(self.detail) + "\n" +\
                "Brief: " + str(self.brief) + "\n" +\
                "Priority: " + str(self.priority) + "\n"

        for service in self.affected_services:
            return_str += (str(service))
            
        return return_str

class SB_Service:
    """
    Service bulletin data for bulletins that affect only a certain subset
    of the system
    """

    # route - route number affected. 
    route = str()

    # direction - direction affected
    direction = str()

    # stop_num - stop number affected
    stop_num = int()

    # stop_name - stop name affected
    stop_name = int()

    def __init__(self, stop_name, route = None, direction = None, stop_num = None):
        # Yes, that's how the spec has it defined. This is wacky.
        # Why would ONLY the stop name be defined?

        log.debug("route in init: " + str(route))

        if (route != None):
            self.route = str(route)
        else:
            self.route = None

        if (direction != None):
            self.direction = str(direction)
        else:
            self.direction = None

        if (stop_num != None):
            self.stop_num = int(stop_num)
        else:
            self.stop_num = None

        self.stop_name = str(stop_name)

    def __str__(self):
        return "AFFECTED SERVICE:\n" +\
                "Route number: " + str(self.route) + "\n" +\
                "Route direction: " + str(self.direction) + "\n" +\
                "Stop number: " + str(self.stop_num)  + "\n" +\
                "Stop name: " + str(self.stop_name) + "\n"

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
