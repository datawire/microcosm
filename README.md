# Datawire Microcosm

Microcosm lets a user simulate 1 or more microservices that are
connected together in different topologies using the Datawire
Microservices Development Kit (MDK).

# Setup 

# Usage

1. Set DATAWIRE_TOKEN in your environment. The value is accessible
   from your Datawire account at http://app.datawire.io.

   `export DATAWIRE_TOKEN='your_token_here'`

2. Install the required Python packages.

   `pip install -r requirements.txt`

3. Launch a scenario. The countdown scenario launches 4 services
   backed by 11 nodes.

   `./microcosm run scenarios/countdown.yml`

   Note that this will launch a number of child processes. Look in
   'logs/countdown' to see the output.

4. Connect to the frontend microservice and get the result. Generally
   this is printed as the first deployed service by the microcosm tool.

   `curl http://127.0.0.1:5000`

   You can check go to the `/text` variant for a more human readable
   version:

   `curl http://127.0.0.1:5000/text`
   
## Terminating the Architecture

When using the 'run' subcommand the microcosm will remain active while
all its subprocesses are running. You can terminate the entire
architecture and all its subprocesses by using control-C.

## Testing the Architecture

In the simple scenario, if you repeatedly connect to the edge service,
you'll see that it load balances automatically between 3 different
intermediary services.

# Defining Architectures

Defining an architecture file is very simple and uses an easy to read
and edit YAML format. Every file should start out with the following
structure:

```yaml
---
description: <a brief description of your simulation>
version: <architecture version>
```

To define the actual topology users should add `services` to the YAML
document such that the doc looks similar to this:

```yaml
description: <a brief description of your simulation>
version: <architecture version>
services:
  <service-name> <service-version>:
    dependencies: [<dep1-name> <dep1-version>, <dep2-name> <dep2-version, ...]
    count: <instance-count>
```

The entries in the `services` structure define the topology. For
example to model a very basic web server and database service use the
following model:

```yaml
description: <a brief description of your simulation>
version: <architecture version>
services:
  frontend 1.0:
    count: 1
    dependencies: [database 1.0, ratings 1.0]
  ratings 1.0:
    dependencies: [database 1.0]
    count: 3
  database 1.0:
    count: 1
```

# Further reading

Microcosm is designed to make it quick and easy to define and deploy
an entire mock microservice application.

Every microservices application is composed of three kinds of services:

 - Edge services: publically addressable services that build on other
   services to provide value directly to the end users of the
   microservices app

 - Intermediate services: services designed primarily for internal use
   that build on and combine what other services provide

 - Foundational services: services that do not have any dependencies

The 'microsym' webapp is a generic server that can be configured to
mimic any kind of service. The 'microcosm' script can deploy it to
mimic any real application topology. You can then drive that topology
with real traffic.

Each node returns a rollup of all the content from its
dependencies. You can therefore connect to any point in the topology
and view the full details of how the request was processed by
examining the content that was returned.

Much inspiration for this is taken from the
[Spigo project](https://github.com/adrianco/spigo) project lets you
simulate interactions between services.
