Election
--------

Election is a simple set of microservices that returns the current
date, and the time remaining until Election Day (November 8, 2016).

Architecture
------------

Election consists of the following microservices:

- Edge
- Time, which returns the current time in GMT
- Countdown, which calculates the time remaining until the election

The topology is:

Edge -> Time
     -> Countdown
