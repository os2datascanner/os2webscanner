.. _faq:

==========================
Frequently Asked Questions
==========================
**Q: How can I mount a shared Windows folder?**

We recommend that you install cifs-utils, by using the following command:

.. code:: console
	
	$ apt-get install cifs-utils 

Afterwards you can mount the folder using the following command:

.. code:: console

	$ mount -t cifs -o username=username //server-name/sharename /mountpoint

**Q: How can I access my lxc localhost from a browser on the host machine?**

Instead of starting your django website on localhost use the lxc containers IP address.
Find the lxc containers IP adress by running the following command when attached to the container:

.. code:: console

	$ ifconfig  

Use the IP address of the container when starting your django website. Access the website on http://%LXC-CONTAINER-IP%:%PORT%.

**Q: How can I access www-data crontab on a production machine?**

.. code:: console

	$ crontab -l -u www-data
