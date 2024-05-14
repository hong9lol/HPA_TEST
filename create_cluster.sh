#!/bin/sh

# delete
# gcloud config set project VALUE

# create
gcloud container clusters create cluster-1 --enable-cloud-run-alpha --enable-kubernetes-alpha --no-enable-autorepair --no-enable-autoupgrade --cluster-version 1.27.6 --region us-central1-a