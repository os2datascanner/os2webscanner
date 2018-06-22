===============
File Scan Setup
===============

Copy static folder to webscanner_site:
.. code:: bash
    $ cp -R django-os2webscanner/os2webscanner/static webscanner_site/static

Create mount directory:
.. code:: bash
    $ sudo mkdir /tmp/mnt
    $ sudo chown -R www-data:www-data /tmp/mnt

Make it possible for www-data to execute mount and umount command:
.. code:: bash
    $ sudo echo "www-data ALL= NOPASSWD: /bin/mount" >> /etc/sudoers
    $ sudo echo "www-data ALL= NOPASSWD: /bin/umount" >> /etc/sudoers