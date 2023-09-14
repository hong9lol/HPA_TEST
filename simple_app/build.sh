#!/bin/sh

if [ "$1" = "local" ]
then 
    echo "local build & run automatically with debug mode"
    GOOS=linux go build -ldflags '-X main.DEBUG=YES' -a -installsuffix cgo -o main .
    ./main
else
    docker build -t simple_app:0.1 .
fi