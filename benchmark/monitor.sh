#!/bin/sh

while true
do
    if [ "$1" = "1" ]; then
        r=`kubectl get pod | grep -v mongo | grep -v memcached | grep -v redis | grep -v media | grep -v jaeger`
    elif [ "$1" = "2" ]; then
        r=`kubectl top pod | grep -v mongo | grep -v memcached | grep -v redis | grep -v media | grep -v jaeger`
    else
        r=`kubectl get horizontalpodautoscalers.autoscaling | grep -v mongo | grep -v memcached | grep -v redis | grep -v media | grep -v jaeger`
    fi  
    clear
    echo "$r"
    sleep 5
done

