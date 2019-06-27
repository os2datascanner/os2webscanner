HOWTO install OS2datascanner on your own server
===============================================

.. warning:: This documentation is outdated. We expect to update it prior to
    the final release of version 3.0.

System requirements
-------------------

We recommend that any server that you wish to use for running this
scanner must have at least 4GB RAM, a CPU with 4 cores and at least as
much free disk space as used by the web sites you want to scan.

The installer only works with Debian-based systems, as it depends on
the ``apt`` package management system. Magenta exclusively supports the
currently supported Ubuntu LTS releases — 16.04 and 18.04 as of this
writing. Any other systems *may* work if you roll the installation manually.

Please note that file scanning relies on the ability to mount SMB/CIFS file
systems, using `mount.cifs <https://linux.die.net/man/8/mount.cifs>`_. This is
is unlikely to work on anything but a native Linux kernel, excluding
operating system virtualisation such as Docker and LXC. Don't expect it to
work in FreeBSD, macOS or Windows either.

Installation directory
----------------------

We recommend that you install the system as a dedicated user, e.g. with
username ``os2``. To proceed with the installation, create the user,
prevent remote login and login as that user:

.. sourcecode:: shell

    sudo adduser os2
    sudo adduser os2 sudo
    sudo su - os2

Note, you are now logged in as the user ``os2``. We assume this in the
rest of this guide. Also note that this is only a convention — you are
free to install the system wherever you want. Paths are not hard-coded
into the system.

.. note:: You should probably remove ``os2``'s sudo rights once the
    installation is complete.

Install Git, Apache and WSGI
----------------------------

.. sourcecode:: shell

    sudo apt-get install git apache2 libapache2-mod-wsgi

Get the code
------------

.. sourcecode:: shell

    git clone https://github.com/magenta-aps/os2datascanner.git

Install Django and Scrapy, including system dependencies
--------------------------------------------------------

.. sourcecode:: shell

    cd os2datascanner
    ./install.sh

You will be prompted for the ``sudo`` password.

.. note:: This requires an Internet connection and may take a while.

Set up the database
-------------------

If you performed the previous step, you've already installed
``postgresql`` and ``postgresql-client``.

Assuming this, do:

.. sourcecode:: shell

    sudo su - postgres
    createuser os2datascanner
    createdb -O os2datascanner os2datascanner
    psql

You may (of course) use another database name, database user etc. as you
please.

Now log out from psql (``\q``) and logout as the postgres user (by
pressing ``Ctrl+D``) to proceed, and return to where you cloned the
``os2datascanner`` source directory (e.g. ``/srv/os2datascanner``).

Next, change into the ``src/os2datascanner/projects/admin`` directory:

.. sourcecode:: shell

    cd src/os2datascanner/projects/admin

Copy the file ``local_settings.py.example`` to ``local_settings.py`` and
open ``local_settings.py`` for editing:

.. sourcecode:: shell

    cp local_settings.py.example local_settings.py
    << edit local_settings.py with your favorite editor>>

In order to make your database setup work, you must override the default
DATABASES configuration.

A sample ``local_settings.py`` configured for your server could look
like this:

.. sourcecode:: python

    SITE_URL = 'http://webscanner.kommune.dk'
    STATIC_ROOT = '/srv/os2datascanner/webscanner_site/static'
    MEDIA_ROOT = '/srv/os2datascanner/webscanner_site/uploads'
    DEFAULT_FROM_EMAIL = 'your@email'
    ADMIN_EMAIL = 'your@email'

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = 'A_LONG_RANDOMLY_GENERATED_SECRET_STRING'

    # Database
    # https://docs.djangoproject.com/en/1.6/ref/settings/#databases

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'os2datascanner',
            'USER': 'os2datascanner',
            'PASSWORD': 'YOUR_PASSWORD',
            'HOST': '127.0.0.1',
        }
    }

Test and initialize
-------------------


.. sourcecode:: shell

    cd /srv/os2datascanner
    source ../python-env/bin/activate
    cd /srv/os2datascanner/src/os2datascanner/projects/admin
    python manage.py test os2datascanner

The test should pass. Now do:

.. sourcecode:: shell

    python manage.py migrate

and create a user with a password you can remember.

Deployment with Apache
----------------------

First, collect content to be served statically:

.. sourcecode:: shell

    cd /srv/os2datascanner/webscanner_site
    python manage.py collectstatic

Next, deploy Apache configuration:

.. sourcecode:: shell

    cd /srv/os2datascanner
    sudo cp config/apache.conf /etc/apache2/sites-available/webscanner

Now, before activating the site, please *edit* the Apache configuration.

-  If you're using SSL, please supply paths to your certificate files.
-  Change the ``ServerName`` directive to the FQDN of your own server.
-  If you're not installing to the directory
   ``/srv/os2datascanner/``, please change all paths accordingly.
-  If you're *not* using SSL, please delete the first VirtualHost,
   specify port 80 for the second one and delete all directives starting
   with the letters “SSL”.

If using SSL, you need to enable the extensions ``mod_rewrite`` and
``mod_ssl``:

.. sourcecode:: shell

    sudo a2enmod rewrite
    sudo a2enmod ssl

You also need to create the Apache log directories:

.. sourcecode:: shell

    sudo mkdir -p /var/log/os2datascanner/

With all this in place, you may now enable the Apache site:

.. sourcecode:: shell

    sudo a2ensite webscanner
    sudo service apache2 restart

The webscanner should now be available at the URL you specified as
ServerName in your VirtualHost, e.g. ``https://webscanner.kommune.dk``.

Start the scanning processors
-----------------------------

First, make the logs directory writable by the web server user:

.. sourcecode:: shell

    sudo chown -R www-data:os2 /srv/os2datascanner/var

Next, start the *process manager* background process in order to get
scans which scan non-text files (e.g. PDF files or Office documents) to
work.

.. sourcecode:: shell

    sudo -u www-data -b /srv/os2datascanner/bin/start_process_manager.sh

.. note:: You may want to have the scanners ``var`` dir somewhere else,
    e.g. in ``/var/lib/os2datascanner``, which is the location we (the
    developers) prefer for production environments. To achieve this, please
    overwrite the Django setting ``VAR_DIR`` in your ``local_settings.py``
    accordingly and set ownership for the directory as indicated above.

Setting up scheduled scans
--------------------------

To setup scheduled scans, you need to add an entry to the user
www-data's crontab:

.. sourcecode:: shell

    sudo crontab -u www-data -e

Add the following line below the commented lines (beginning with '#'),
and then save the file::

    */15 * * * *    /srv/os2datascanner/cron/run_cron_script.sh

Setting up scheduled summary reports
------------------------------------

The system may send out summary reports describing the performance,
results, etc., of different scanners.

To have summaries emailed to recipients, edit ``crontab`` as described
in the previous section, adding the line::

    0    7 * * * /srv/os2datascanner/cron/dispatch_summaries.sh

to have summaries emailed every day at 7AM. You can of course change
this as you wish, but summaries should be mailed no more than once a day
as this may cause reports to be sent twice.

Creating an organization and adding a user to it:
-------------------------------------------------

Visit your webscanner site URL + ``/admin/`` to enter the Django admin
interface.

Login with the Django superuser you created (when running
``python manage.py syncdb``). Click on “Organization” and hit the button
labeled “Tilføj Organisation” or “Add Organization” to add an
“Organization”. This is necessary — the system will not work without at
least one organization. Give your new organization a name, email address
and phone number and save it by clicking “Gem” or “Save” at the bottom
of the page.

Return to the main admin page and click “Brugere”. Click the username
that you would like to add to the organization.

At the bottom of the page, under “User profiles”, change the
“Organisation” to the organization you created and save.

OS2datascanner is now ready to be used.
