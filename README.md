# Datawire Microcosm

Microcosm lets a user simulate 1 or more microservices that are connected together in different topologies using the Datawire Microservices Development Kit (MDK).

# Setup 

Install the Datawire MDK if you have not already done so:

`curl -sL https://raw.githubusercontent.com/datawire/mdk/develop/install.sh | bash -s -- --python develop`

# Usage

1. Set DATAWIRE_TOKEN in your environment. The value is accessible
   from your Datawire account at http://app.datawire.io.

   `export DATAWIRE_TOKEN='your_token_here'`

2. Install the required Python packages.
   `pip install -r requirements.txt`

3. Launch a scenario. The simple scenario launches 5 microservices.

   `python microcosmctl.py run scenarios/countdown.yml`

4. Connect to the edge microservice and get the result. Generally this is printed as the first deployed service by the `microcosmctl.py` tool.

   `curl http://127.0.0.1:5000`
   
## Terminating the Architecture

When using the 'run' subcommand the microcosmctl will remain active
while all its subprocesses are running. You can terminate the entire
architecture and all its subprocesses by using control-C.

## Testing the Architecture

In the simple scenario, if you repeatedly connect to the edge service,
you'll see that it load balances automatically between 3 different
intermediary services.

# Defining Architectures

Defining an architecture file is very simple and uses an easy to read and edit YAML format. Every file should start out with the following structure:

```yaml
---
description: <a brief description of your simulation>
version: <architecture version>
```

To define the actual topology users should add `services` dictionary to the YAML document such that the doc looks similar to this:

```yaml
description: <a brief description of your simulation>
version: <architecture version>
services:
  frontend:
    count:1
```

The entries in the `services` dictionary define the topology. For example to model a very basic web server and database service use the following model:

```yaml
description: <a brief description of your simulation>
version: <architecture version>
services:
  frontend:
    version: 1.0
    count: 1
    dependencies: [database]
  contacts_service:
    version: 1.0
    count: 3
    dependencies: []
```

# Further reading

Every microservices application is composed of three kinds of services:

* Edge services: publically addressable services that build on other
services to provide value directly to the end users of the
microservices app

* Intermediate services: services designed primarily for internal use
that build on and combine what other services provide

* Foundational services: services that do not have any dependencies

The [Spigo project](https://github.com/adrianco/spigo) lets you
simulate interactions between services.
