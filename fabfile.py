''' Fabric's fabfile for use on the devhost. Invoke this with::

    fab --list
'''

from fabric.api import env
from fabric.api import local
from fabric.api import run
from fabric.api import sudo
from fabric.api import task
from fabtools.vagrant import vagrant
from fabtools.vagrant import vagrant_settings


DEPLOY_ROOT = '/srv/councilroom'
DEPLOY_USER = 'cr_prod'


@task
def clean():
    ''' Clean the local directory of unnecessary files
    '''
    local("find . -type f -name '*~' -print0 |xargs -0 rm -f")
    local("find . -type f -name '*.pyc' -print0 |xargs -0 rm -f")


@task
def build():
    ''' Build the app within the Vagrant host
    '''
    with vagrant_settings():
        # Blow away and recreate the deployment directory
        sudo("echo rm -rf {0}".format(DEPLOY_ROOT), user=DEPLOY_USER)

        # Create the virtualenv in which the application runs

        # Create the static directory from which Nginx will serve
        # necessary files

        # Copy our images, CSS, JavaScript, etc. into the serving
        # directory

        # Download and install Bootstrap and other external JavaScript
        # packages


