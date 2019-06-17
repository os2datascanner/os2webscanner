HOWTO get the system up and running for development
---------------------------------------------------

.. highlight:: shell

This document explains how to get the source code, set up the database, run the
tests and boot the development server.  Get the code::

  $ git clone https://github.com/os2webscanner/os2webscanner.git

Install Django and Scrapy, including system dependencies::

  cd os2datascanner
  ./install.sh

.. note:: The installation will try to install all needed system
          packages not present on a fresh install of Ubuntu. This part
          of the installer uses ``apt-get install`` and has only been
          tested with Ubuntu.

Once ``install.sh`` has succeeded, proceed to the next section.

Set up the database
===================

If you performed the previous step, you've already installed ``postgresql`` and
``postgresql-client``.

Assuming this done::

  sudo su - postgres
  createdb os2datascanner
  createuser os2datascanner
  psql


The following commands must be executed *within* the PostgreSQL
interactive session:

.. sourcecode:: sql

  GRANT ALL ON DATABASE os2datascanner TO os2webscanner;
  ALTER USER os2datascanner WITH PASSWORD 'os2webscanner'; 
  ALTER USER os2datascanner CREATEDB;

If you choose any other password, please change in ``settings.py``. The last
``ALTER USER`` is to enable the test suite to run on PostgreSQL.

Now log out from psql and the postgres user to proceed, returning to
where you cloned the os2datascanner source directory.

Test and initialize
===================

To set up a testing environment, run::

   cd scrapy_webscanner
   python -m unittest discover tests
   cd ..

These tests should pass::

  cd webscanner_site
  source ../python-env/bin/activate
  python manage.py test

The test should pass. Now do::

  python manage.py migrate

and create a user with a password you can remember.


Start the system with::

  python manage.py runserver 8080

and access the admin system at http://localhost:8080/admin/.


Start the scanning processors
=============================

You need to start the process manager background process in order to get actual
scans done::

  cd /home/os2/os2datascanner
  source python-env/bin/activate  # If not active already
  python scrapy-webscanner/process_manager.py &


That's it!

