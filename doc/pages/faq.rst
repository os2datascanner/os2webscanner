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

**Q: How can I set up the datascanner-manager as a system service on the development machine**

Assuming You have put Your code in os2webscanner in your home directtory, You should copy the following file to
/etc/systemd/system/datascanner-manager.service after changing **YOU** in the following file to Your own username

.. code:: console

    [Unit]
    Description=Datascanner-manager service
    After=network.target

    [Service]
    Type=simple
    User=YOU
    WorkingDirectory=/home/YOU/os2webscanner
    ExecStart=/home/YOU/os2webscanner/python-env/bin/python  /home/YOU/os2webscanner/scrapy-webscanner/scanner_manager.py
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target

After that run

.. code:: console

    sudo systemctl enable datascanner-manager
    sudo systemctl start datascanner-manager

Be advised that You have to restart it whenever You make code changes to any of the modules it uses

