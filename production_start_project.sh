#!/bin/bash
echo Stop  Application

kill -TERM $(cat mini_erp.pid)

sleep 1s
ps ax|grep gunicorn
echo Stop minierp Gunicorn

echo Starting Gunicorn and active virtualenv
# virtualenv for production.
source .venv/bin/activate
#source /home/ubuntu/PycharmProjects/djangoGunicorn/bin/activate

gunicorn -c erp_deploy.py
sleep 1s
ps ax|grep gunicorn

#Deactivate Virtual env for production

deactivate
echo virtualenv deactivate