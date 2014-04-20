#!/bin/bash

for json in $(ls jsons/*.json)
do
    echo STARTING RUN FOR $json;
    echo -------------------------------;
    cp $json test.json;
    echo $(python3 lamp_stack_times_reqs.py)
    echo ;
done

