dominionstats
=============

This is the code behind http://councilroom.com. Feel free to fork it to make
it do interesting new things.

The project is currently run by Mike McCallister
(mike@mccllstr.com). The maintainer "emeritus" is rrenaud
(rrenaud@gmail.com), with contributions so far by Larry, rspeer, David
Lu, and tlstyer.


Setup for Local Development
===========================

This project now includes files to enable you to use Vagrant
(http://www.vagrantup.com) to create isolated environments for
development, testing, and production release builds. This is much
easier to recreate than trying to install all the pieces following the
Installation instructions below.

This Vagrant-based model splits activity into separate
environments. The first of these is your *development host*. The
development host is where high-level tools that manage the other
environments run. This is where you will checkout and edit the source
code. Unlike many models where development and testing is done on the
local machine, you will not install the application here.

The next environment is the *development guest*. A development guest
is a temporary virtual machine instance where the application will
actually be installed and run. These environments will contain the
numerous pieces that are required to run the application in a tidy,
easy to recreate package.

To set up your development host, use the following steps. This is a
one-time activity.

#. Install the appropriate version of VirtualBox
   (https://www.virtualbox.org/) for your host machine.

#. Install the appropriate version of Vagrant
   (http://www.vagrantup.com) for your host machine.

#. Install `virtualenv`, `pip`, and `git`. This depends on the
   platform you are using as your development host.

     * On an Ubuntu machine, the required commands are::

	 sudo apt-get install python-virtualenv python-pip git

     * On a Windows PC, the necessary steps are:

       #. TODO

With the above steps completed, you are ready to get a local copy of
the source code and launch the development guest. Use the following
steps:

#. Clone the source code repository to your machine. In this example,
   the source code will go into the directory named `dev`::

     git clone git@github.com:mikemccllstr/dominionstats.git dev

#. Switch to the repository clone and setup the virtual environment
   that will be needed for tools that run on the development host
   itself::

     cd dev
     virtualenv .venv-devhost
     . .venv-devhost/bin/activate
     pip install -r requirements/devhost.txt

The above steps typically only need to be done once per local copy of
the source code. Once you have this done, each time you want to do
some development, you will repeat the following steps:

#. Activate the devhost virtual environment, launch the Vagrant
   instance, and ssh into it::

     cd dev
     . .venv-devhost/bin/activate
     vagrant up
     vagrant ssh

#. From within the Vagrant instance, you can import a day's worth of
   data and then launch the web application with the following
   commands::

     cd /vagrant
     virtualenv


Installation
====

Turbo frontend javascript hacking
====
super easy frontend modifications without any server setup::

     checkout code from github.
     google-chrome --allow-file-access-from-files
     browse to local html pages (eg, dominionstats/supply_win.html).
     edit local javascript files.

I just want access to some data!
====
Send (rrenaud@gmail.com) a mail and I'll see what I can do.

Long, arduous but incredibly rewarding full setup
====
The code depends on:

- Python version 2.6 or 2.7
- mongodb (http://www.mongodb.org) (1.5.3+ or later)
- pymongo (http://api.mongodb.org/python/1.9%2B/index.html)
- web.py (http://webpy.org)
- argparse (included in Python 2.7/3.2)
- simplejson (http://pypi.python.org/pypi/simplejson/)

Ubuntu Installation Commands for pymongo and webpy::

     sudo pip install pymongo
     sudo easy_install web.py
     mkdir db

Run an instance of mongodb with::

     mongod --dbpath=db

After install those packages, the system can be setup by running the
update_loop.py script, which will take a few hours to download one months of
games logs from councilroom, and then parse through it all and load it into a
database::

     python update_loop.py
These instructions are outdated and no longer work. Use update.py, which is run through a worker script.


And after that is down, this starts webserver running on localhost:8080::

     python frontend_local.py

Hacking Guidelines
====
Python code:
  - Write it in pep8, even if I didn't all the time.
  - Wrap lines at 80 characters.
  - Try not to write super long functions, break them up into logical subfunction even if those functions are only called once.

  - Did you see something in the code is fugly and offends your natural sense of what is good in the world?  I'll happily take style cleanups.

  - Anatomy of an analysis.
     + Want analysis to be incremental, can go day at a time.
        * Use an incremental_scanner.
        * Prefer using game.Game objects over raw game docs from the database.  game.Game objects are easier to work with, and make maintenance easier.
        * Since we want to be incremental, store raw counts in database, normalize them with divisions, etc at presentation time.
        * Want to keep track of a random variable that has some kind of spread? Use a stats.MeanVarStat.
        * Consider using primitive_util for serializing/deserializing objects that store the aggregate information.

  - How to do display?
      + Lots of existing server side templating in Python.
      + Prefer templates to programatically building up strings (even if if the existing code doesn't always).
      + Seriously consider outputting JSON from server like (/supply_win_api) and doing presentation in javascript (/supply_win), since it allows frontend development without running the whole system.

JavaScript code:
  * Keep non-trivial bits of JavaScript in separate .js files rather than embedded in HTML.  It makes my Emacs happier.

Got a technical problem/question/idea?  You can send an email to the dev group,

https://groups.google.com/forum/?fromgroups#!forum/councilroom-dev

Happy hacking.
