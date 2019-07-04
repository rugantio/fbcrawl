#!/usr/bin/env bash

OLD=$PWD
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd $DIR

if [ -d "/usr/local/crawler-venv" ]
then
  source /usr/local/crawler-venv/bin/activate
fi

FOLDER=$(date +"%Y-%m")
mkdir -p "$OLD/$FOLDER"

DAY=$(date +"%d")
mkdir -p "$OLD/$FOLDER/$DAY/facebook"

TIME=$(date +"%s")

source ~/.secrets

scrapy crawl events -a email="$FACEBOOK_EMAIL" -a password="$FACEBOOK_PASSWORD" -a page="$1" -o "$OLD/$FOLDER/$DAY/facebook/$TIME_$1.csv"
