Microcosm Plan
==============

Microcosm is designed to make it quick and easy to define and deploy
an entire mock microservice application.

Every microservices application is composed of three kinds of services:

 - Edge services: publically addressable services that build on other
   services to provide value directly to the end users of the
   microservices app

 - Intermediate services: services designed primarily for internal use
   that build on and combine what other services provide

 - Foundational services: services that do not have any dependencies

We can easily build a simple generic server that can be configured to
mimic each kind of service. Once we have this, we can deploy it to
mimic any real application topology we can think of and even drive
that topology with real traffic.

Each server will collect deployment and operational telemetry data
during runtime in a way that allows us to read back the logs and get a
good view of what has actually occurred.

We will start super simple with a python requests/flask based
implementation of this thing and use simple manual deployment on EC2
instances. As we learn more/streamline more we may add implementations
in other languages and/or frameworks into the mix as well as other
deployment mechanisms.

Details
=======

Build a simple microservices application that handles incoming
requests by using discovery to query a configurable set of downstream
services, concatenate all their responses, and return them to the
upstream service along with a unique request-id that it supplies by
itself.

This one simple server can function as a foundation, intermediate, or
edge service depending on how it is configured. If it is configured to
have zero dependencies, then it will respond with only a unique
request-id and function in the role of a foundational service. If it
is configured to have some dependencies and is running on a transient
address then it is functioning in the role of an intermediate
service. If it is configured to have some dependencies and is deployed
behind a well known load balancer then it is functioning in the role
of an edge service.

There may be several layers of backend service nodes in a deployed
topology. Keeping the system simple and closely aligned with our
hypothetical first customer is important, therefore, use Python along
with Requests and Flask library to facilitate interservice
communication. The project MUST NOT use Quark to generate contracts
and connect services as we need to simulate expected customer usage in
the immediate future.

The service nodes SHOULD NOT have “real” business logic other than to
receive requests, produce a result, and send a response. Services MUST
log all high-level events that occur (e.g. SERVICE UP, SERVICE DOWN,
REQUEST SENT/RECEIVED, RESPONSE SENT/RECEIVED, RESULT PRODUCED, ERROR
etc.). The system MUST have a synchronized clock that yields a
consistent view of time when all logged operations are processed.

There MUST be a simple mechanism for configuring how the server
behaves, i.e. its role in the overall topology.

Future stuff:

 - Figure out something other than manual deployment.
 - Simulate errors.
