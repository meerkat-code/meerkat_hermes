#!/bin/bash
ssh mhs '
ssh hermes "
cd /var/www/meerkat_hermes;
sudo git checkout master;
sudo stash;
sudo git pull;
sudo stop uwsgi-hermes;
sudo start uwsgi-hermes" '