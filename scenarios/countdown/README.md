Countdown
---------

Countdown is a simple set of microservices that returns the current
date and the time remaining to various world events.

Architecture
------------

Election consists of the following microservices:

- Edge
- Time, which returns the current time
- Countdown, which calculates the time remaining until the election

The topology is:

Edge -> Time
     -> Election
     -> Olympic2018