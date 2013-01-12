#!/bin/sh

DEPLOYMENT_DIR=/srv/councilroom/councilroom_prod
VENV_DIR=$DEPLOYMENT_DIR/.venv-prod

# Run the update script
cd $DEPLOYMENT_DIR
$VENV_DIR/bin/python update.py --debug

# Schedule this script to be run again at 3am the next morning.
at 3am <<EOF
$0
EOF
