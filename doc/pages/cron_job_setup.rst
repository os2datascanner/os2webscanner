.. _setupcronjobs:

=========================
How to setup cronjobs
=========================

**Intro**

This guide is cronjob setup instructions for production purposes. The files can be found under %PROJECT_DIR%/cron.
It is necessary to setup different cron jobs before you can take advantage of all OS2Datascanner funtionality.
Here I will go through what the different cronjobs do and what is best practise when you set them up.

**How to**

As we are running apache2 in front it is important that the cronjobs are setup for user www-data.
To access and edit www-data crontab do the following:

.. code:: console

	$ sudo -u www-data crontab -e

**Best practice**

You can find an example of a crontab file used in production under %PROJECT_DIR%/cron/crontab-example.txt

* The run_cron_script.sh file should run quite often as it the job responsible for starting scheduled scan jobs.
* The monitor_pm.sh is monitoring the process_manager and should there for run at least once an hour.
* The dispacth_summaries.sh is as it say dispacthing report summaries. I would suggest to let it run once a week.
* The run_exchange_cron_script.sh is downloading exchange mailbox content based on the exchange domains created through the webinterface. Download exchange content can create a heavy load on the exchange server and therefore I suggest to let in run during the weekends and at least once a week.