#!/bin/bash

export DATAWIRE_PLATFORM_TYPE=blah
export DATAWIRE_ROUTABLE_HOST=127.0.0.1

python ../../microcosm.py edge.yml > edge.log 2>&1 &
python ../../microcosm.py time.yml > time.log 2>&1 &
python ../../microcosm.py countdown.yml > countdown.log 2>&1 &

