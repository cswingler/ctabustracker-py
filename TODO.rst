====
TODO
====

 * Sanitize directions! If you don't enter the expected case and spacing, 
   you'll get nothing!
 * In the Service_Bulletin object, add a method to strip the brief result of
   any HTML that may be passed along.
 * Fix Exceptions
 * Implement handling of errors from the API
 * Documentation
 * Working around the weirdness in the spec. Like page 28 and the 
   affectedservice object, why would you have nothing in there
   EXCEPT the name of the stop?
 * Testing against the API, as the documentation doesn't match up
   with the results often.
 * Logging: More performance and debugging logging as necessary, allow 
   adjustment
 * Error handling: Errors returned from the CTA API will be silently ignored or
   throw an unexpected exception, should pass those out as necessary
 * Caching: Shouldn't make a request against the API more than once every 60 
   seconds, as the data on the API only updates that frequently
 * Utility methods: Calculating distance between two points on a route
 * Coherency: There's some weirdness in the BusTracker API that exists here,
   particularly with terse ("A" for arrival and "D" for departure) or verbose
   ("West Bound") string handling. This should probably be more consistent.
 * __str__() methods: Ugly.
 * Exceptions: a mess.
 * General cleanup: It's been a while since I've written anything in Python, a
   lot of this code is just a mess.

