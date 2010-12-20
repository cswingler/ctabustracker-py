================
ctabustracker.py
================
---------------------------------------------------------
A Python module for accessing CTA Bus Tracker information
---------------------------------------------------------

About
=====
This implements all of the methods available in the Chicago Transit Authority
Bus Tracker API. (see http://www.transitchicago.com/developers/bustracker.aspx 
for more information)

Usage
=====

Setup
-----
Before you can start with anything, you need to create a ctabustracker object,
and set it up with your API key.

::

 c = ctabustracker.ctabustracker("i28bcs01q1YV1CfAd1GcVK1q4")

Examples
--------
After instantiating the ctabustracker class, you can get some information out of it.

Getting scheduled arrivals for a stop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Say you want to figure out when buses are scheduled to arrive at the stop at 
76th Street & Ford City Movie Theatre for the #54B South Cicero bus, going 
North bound.

First, you'll need to get a list of stops to figure out what stop number is
at that location. Use ``getroute_stops()`` to get a list of stops::
 
 >>> stops = c.getroute_stops("54B", "North Bound")

Note that the case and whitespace in the second parameter must be exact - 
title case, and a space between the direction and "bound". [#fixme]_

Next, search through the list of stops to find the one you're looking for::

 >>> for stop in stops:
 ...  if (stop.stop_name == "76th Street & Ford City Movie Theatre"):
 ...   break
 ... 
 >>> print stop
 Stop #: 15935 | Stop name: 76th Street & Ford City Movie Theatre | Latitude: 41.754317884449 | Longitude: -87.733882069588
 
Then, just pass this stop_id into ``getpredictions_stop()``::

 >>> predictions = c.getpredictions_stop(stop.stop_id)
 >>> for prediction in predictions:
 ...  print prediction
 ... 
 PREDICTION:
 Prediction generated at: Sun Dec 19 19:25:00 2010
 Type: A
 Route: 54B
 Direction: North Bound
 Route destination: Cermak/Kenton
 Stop number: 15935
 Stop name: 76th Street & Ford City Movie Theatre
 Vehicle number:  1866
 Distance away: 4941
 Estimated time of arrival: Sun Dec 19 19:32:00 2010
 Minutes to arrival (at instantiation): 7
 PREDICTION:
 Prediction generated at: Sun Dec 19 19:26:00 2010
 Type: A
 Route: 79
 Direction: East Bound
 Route destination: Lakefront
 Stop number: 15935
 Stop name: 76th Street & Ford City Movie Theatre
 Vehicle number:  6451
 Distance away: 2129
 Estimated time of arrival: Sun Dec 19 19:34:00 2010
 Minutes to arrival (at instantiation): 8

**Caution**: The "Minutes to arrival" (``Prediction.mins_to_arrival_at_init``) 
return value *DOES NOT* update past the initial instantiation of the 
Prediction object (created here by calling 
``ctabustracker.getpredictions_stop()``).  If you want an update, you'll either
need to call this again to generate a new Prediction object (which is the most 
accurate, as it will make another call against the BusTracker API), or use 
the member function of Prediction ``Prediction.estimated_time_to_arrival()``.

Getting service bulletins for routes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, we're going to get all service bulletins published for routes 
21 (Cermak) and 135 (Clarendon/LaSalle Express).

::

 >>> bulletins = c.getbulletins_route(21, 135)
 >>> for bulletin in bulletins:
 ...  print bulletin
 ... 
 SERVICE BULLETIN:
 Name: Bus Stop Added - #21 Cermak
 Subject: New Bus Stop Added
 Detail: Effective Wed, March 10<br/><br/>A new northbound bus stop will be added on the northeast corner at King Drive/25th. <br/>Bus stop is being added for customer convenience.
 Brief: None
 Priority: Low
 AFFECTED SERVICE:
 Route number: 21
 Route direction: None
 Stop number: None
 Stop name: None
 AFFECTED SERVICE:
 Route number: 21
 Route direction: None
 Stop number: None
 Stop name: None
 AFFECTED SERVICE:
 Route number: 135
 Route direction: None
 Stop number: None
 Stop name: None
 AFFECTED SERVICE:
 Route number: 136
 Route direction: None
 Stop number: None
 Stop name: None
 
 SERVICE BULLETIN:
 Name: Reroute and Temporary Bus Stop Relocation - #21
 Subject: Reroute/ Bus Stop Relocation
 Detail: Buses will be rerouted  for customer convenience to serve the temporary 'L' station entrance on Archer Avenue while we perform station construction to modernize the Cermak-Chinatown station.<br/><br/>Temporary Reroute: Buses will operate in both directions via Cermak, Wentworth, Archer, Clark, and Cermak. Allow extra travel time. <br/><br/>Temporary Bus Stop Relocation:<br/>The eastbound #21 Cermak bus stop on the southwest corner of Cermak/Wentworth will be temporarily discontinued. <br/><br/>Board eastbound buses: <br/><br/>. on Wentworth Avenue a half block north of Cermak Road, or <br/>. on Archer Avenue east of Wentworth, in front of the new auxiliary station entrance. <br/><br/>The westbound bus stop on Cermak Road in front of the Red Line station entrance will be temporarily discontinued. Board westbound buses: <br/><br/>. on the southwest corner of Wentworth/Archer, or <br/>. on the northwest corner of Wentworth/Cermak.<br/><br/>
 Brief: None
 Priority: Low
 AFFECTED SERVICE:
 Route number: 21
 Route direction: None
 Stop number: None
 Stop name: None
 AFFECTED SERVICE:
 Route number: 21
 Route direction: None
 Stop number: None
 Stop name: None
 AFFECTED SERVICE:
 Route number: 135
 Route direction: None
 Stop number: None
 Stop name: None
 AFFECTED SERVICE:
 Route number: 136
 Route direction: None
 Stop number: None
 Stop name: None
 
 SERVICE BULLETIN:
 Name: #135, #136 Temporary Bus Stop Changes
 Subject: Wacker Drive Reconstruction
 Detail: The northbound bus stop located on the southeast corner at Franklin/Jackson has been temporarily eliminated. <br/><br/>A temporary northbound bus stop has been added on the southeast corner at Jackson/Franklin.<br/><br/>Bus stops have been eliminated or added due to the Wacker Drive Reconstruction Project.<br/>
 Brief: None
 Priority: Low
 AFFECTED SERVICE:
 Route number: 21
 Route direction: None
 Stop number: None
 Stop name: None
 AFFECTED SERVICE:
 Route number: 21
 Route direction: None
 Stop number: None
 Stop name: None
 AFFECTED SERVICE:
 Route number: 135
 Route direction: None
 Stop number: None
 Stop name: None
 AFFECTED SERVICE:
 Route number: 136
 Route direction: None
 Stop number: None
 Stop name: None

There are a few things to note that are going on here:
 * Each ``Service_Bulletin`` object can contain a ``SB_Service object``.  The 
   ``SB_Service`` object contains a CTA service (a stop or a route) that is
   affected by this bulletin.
 * This is where the CTA BusTracker API specification deviates greatly from the
   resulting data.  The  ``Service_Bulletin.brief`` result appears to never be
   used (which is unfortunate for small-screen devices)
 * Note that the ``Service_Bulletin.detail`` result has HTML tags in it.


Member Functions
----------------
These should all be documented for the most part by pydoc.  Point pydoc
to this module, or see the ctabustracker.html file supplied.

Classes
-------
Be sure to also take a look at the classes themselves.  Most are simply
similar to C-style structs, that is, a container for data of differing 
types. 


.. [#fixme] Denotes an egregrious bug that should be fixed

.. vim: set ft=rst
