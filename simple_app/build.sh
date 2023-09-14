#!/bin/sh

if [ "$1" = "local" ]
then 
    echo "local build & run automatically with debug mode"
    GOOS=linux go build -ldflags '-X main.DEBUG=YES' -a -installsuffix cgo -o main .
    ./main
else
    echo "docker build and push to docker hub, required docker login"
    docker build -t hong9lol/simple_app .
    docker push hong9lol/simple_app
fi