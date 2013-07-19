#!/bin/bash

# Make sure we've got the latest code
git pull

# Update the virtual environment
virtualenv .venv-worker
. .venv-worker/bin/activate
pip install -r requirements-worker.txt 

celery worker --app=background -l info -f worker.log
