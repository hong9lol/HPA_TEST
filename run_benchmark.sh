#!/bin/sh
raw_url=`cat target_url.txt`
url=$(echo $raw_url | tr "\"" "\n")
python3 ./benchmark/run.py -u $url