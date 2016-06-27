# Datawire Microcosm

Microcosm lets a user simulate 1 or more microservices that are connected together in different topologies using the Datawire Microservices Development Kit (MDK).

# Setup 

Install the Datawire MDK if you have not already done so:

`curl -sL https://raw.githubusercontent.com/datawire/mdk/master/install.sh | bash -s -- --python develop`

# Usage

1. Set DATAWIRE_TOKEN in your environment. The value is accessible
   from your Datawire account at http://app.datawire.io.

   `export DATAWIRE_TOKEN='your_token_here'`

2. Launch a scenario. The simple scenario launches 5 microservices.

   `python microcosmctl.py scenarios/countdown.yml`

3. Connect to the edge microservice and get the result. Generally this printed as the last deployed service by the `microcosmctl.py` tool.

   `curl http://127.0.0.1:5000`

In the simple scenario, if you repeatedly connect to the edge service,
you'll see that it load balances automatically between 3 different
intermediary services.

# Defining Architectures

Defining an architecture file is very simple and uses an easy to read and edit YAML format. Every file should start out with the following structure:

```yaml
---
name: <name of your architecture>
description: <a brief description of your simulation>
version: <architecture version>
```

To define the actual topology users should add `services` dictionary to the YAML document such that the doc looks similar to this:

```yaml
name: <name of your architecture>
description: <a brief description of your simulation>
version: <architecture version>
services:
  frontend:
    count:1
```

The entries in the `services` dictionary define the topology. For example to model a very basic web server and database service use the following model:

```yaml
name: <name of your architecture>
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

