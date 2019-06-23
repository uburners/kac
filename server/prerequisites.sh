#!/bin/sh

set -e


sudo apt-get update
sudo apt-get install python3-pip python3-virtualenv python3-ipython 

pip3 install -r requirements.txt

https://github.com/jjhelmus/berryconda

apt-get install postgresql-9.6 postgresql-client-9.6 postgresql-contrib-9.6

sudo -u postgres -H createuser -l kac -P
sudo -u postgres -H createdb -O kac kac

sudo -u postgres -H createdb psql -1 -e -f schema.sql

