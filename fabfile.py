''' Fabric's fabfile for use on the devhost. Invoke this with::

    fab --list
'''

from fabric.api import env
from fabric.api import local
from fabric.api import put
from fabric.api import run
from fabric.api import sudo
from fabric.api import task
from fabric.context_managers import cd
from fabtools.vagrant import vagrant
from fabtools.vagrant import vagrant_settings


DEPLOY_ROOT = '/srv/councilroom'
DEPLOY_USER = 'cr_prod'
DEPLOY_GROUP = 'cr_prod'


@task
def clean():
    ''' Clean the local directory of unnecessary files
    '''
    local("find . -type f -name '*~' -print0 |xargs -0 rm -f")
    local("find . -type f -name '*.pyc' -print0 |xargs -0 rm -f")


@task
def build():
    ''' Build the app within the Vagrant host

    The strategy being followed here is to use Ansible (as invoked by
    `vagrant up` or `vagrant provision`) to manage OS-level
    packages.

    Once Ansible has set up the environment, this Fabfile is
    responsible for turning the contents of the current working
    directory (typically a check out of the source code repository)
    into a "built" version of the application within the Vagrant
    host. "Building", in this case, means installing all the
    appropriate versions of the Python dependencies in a standalone
    VirtualEnv, downloading and installing JavaScript libraries that
    CouncilRoom depends upon, compiling any CoffeeScript/Less/Sass or
    related assets, minifying images and other static files, etc.

    That working version can be used for development and testing
    purposes. Ultimately, it will be converted into a Deb package for
    deployment into the production environment.
    '''

    # Do the following on the vagrant host itself
    with vagrant_settings():
        # Blow away and recreate the deployment directory
        sudo("rm -rf {0}".format(DEPLOY_ROOT), user='root')
        sudo("mkdir {0}".format(DEPLOY_ROOT), user='root')
        sudo("chown {1}:{2} {0}".format(DEPLOY_ROOT, DEPLOY_USER, DEPLOY_GROUP),
             user='root')
        sudo("chmod ug=rwx,o=rx {0}".format(DEPLOY_ROOT), user='root')

        # Create the virtualenv in which the Council Room application
        # and its Python dependencies will be installed and run
        with cd(DEPLOY_ROOT):
            sudo("virtualenv --no-site-packages cr-venv",
                 user=DEPLOY_USER)
            put(local_path='requirements', remote_path='.', use_sudo=True)
            sudo("cr-venv/bin/pip install -r requirements/web.txt",
                 user=DEPLOY_USER)
            sudo("cr-venv/bin/pip install -r requirements/background.txt",
                 user=DEPLOY_USER)
            sudo("rm -rf requirements", user='root')

        # Create the static directory from which Nginx will serve
        # necessary files

        # Copy our images, CSS, JavaScript, etc. into the serving
        # directory

        # Download and install Bootstrap and other external JavaScript
        # packages


