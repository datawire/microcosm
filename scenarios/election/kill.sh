#!/bin/bash

ps waxu | fgrep microcosm | fgrep -v grep | awk '{print $2}' | xargs kill
