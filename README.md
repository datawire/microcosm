# Datawire Microcosm

Microcosm lets a user simulate 1 or more microservices that are
connected together in different topologies using the Datawire
Microservices Development Kit (MDK).

# Usage

1. Set DATAWIRE_TOKEN in your environment. The value is accessible
   from you Datawire account at http://app.datawire.io.

   export DATAWIRE_TOKEN='your_token_here'


2. Launch a scenario. The simple scenario launches 5 microservices.

   scenario/simple/launch.sh

3. Connect to the edge microservice and get the result.

   curl http://localhost:5000

In the simple scenario, if you repeatedly connect to the edge service,
you'll see that it load balances automatically between 3 different
intermediary services.
