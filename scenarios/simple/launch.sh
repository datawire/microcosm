#!/bin/bash

export DATAWIRE_PLATFORM_TYPE=blah
export DATAWIRE_ROUTABLE_HOST=127.0.0.1

python ../../microcosm.py edge.yml > edge.log 2>&1 &
python ../../microcosm.py intermediary1.yml > intermediary1.log 2>&1 &
python ../../microcosm.py intermediary2.yml > intermediary2.log 2>&1 &
python ../../microcosm.py intermediary3.yml > intermediary3.log 2>&1 &
python ../../microcosm.py foundational.yml > foundational.log 2>&1 &
