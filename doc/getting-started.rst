Getting started with OS2datascanner
***********************************

An overview of the system
=========================

An OS2datascanner installation consists of three components: the
*administration interface* (a Django app), the *scanner engine* (a set of
system services), and the *report interface* (another Django app).

The administration interface is used to build up scanner jobs: sources of
scannable things and rules to search for in them. The details of these jobs are
stored in a PostgreSQL database. It's intended for use by an organisation's
administrators or data protection officers.

The scanner engine, also known as the *pipeline*, consists of five *stages*
built around RabbitMQ message queues. Each of these stages is a program that
reads a message, carries out a small, simple job, and then sends one or more
messages to another stage. At a high level, the scanner engine receives scan
requests from the administration interface and produces scan results.

The report interface displays the results of the scanner engine. It shows
matched objects and details of why they were matched, and allows users to flag
certain results as irrelevant. It's intended for use by all of an
organisation's employees.

Installing the system
=====================

Installing OS2datascanner as a whole requires root-level access, and the
installation process will configure and manipulate operating system-level
services. As such, development environments should normally be installed in an
appropriate virtual machine.

(Note that some parts of OS2datascanner *are* suitable for use in a normal
Python environment:

* the ``os2datascanner.engine2.rules`` module, which defines search rules,
  logical operators, and content conversions; and
* the ``os2datascanner.engine2.model`` module and its submodules, which define
  sources of scannable things and exploration strategies.

This is partly a principled decision to keep the scanner engine loosely coupled
to the rest of the system, and partly a practical move to make development
easier, as most new development takes place in these packages.)

Preparing the Python environment
--------------------------------

From the installation folder, run the ``install.sh`` script as root; this will
install all of the necessary system dependencies and set up a Python virtual
environment in the ``python-env/`` folder.

Preparing the Django environments
---------------------------------

From the installation folder, run the ``setup/admin_module.setup.sh`` script as
root to set up the database for the administration interface. Then run
``setup/report_module.setup.sh`` to do the same for the report interface.

Preparing Prometheus (optional)
-------------------------------

OS2datascanner's pipeline uses Prometheus to provide live status monitoring. To
configure a local Prometheus server to collect data from the pipeline
components, run the ``setup/prometheus_setup.sh`` script as root.

Starting the system
===================

For debugging, it's often easiest to start all of the OS2datascanner components
in a terminal. The ``bin/`` folder contains a number of convenience scripts for
doing this:

- ``bin/pex`` runs its command-line arguments in the context of the Python
  virtual environment and with a working directory of ``src/``. (The rest of
  the scripts are built around this command.)
- ``bin/manage-admin`` runs the Django ``manage.py`` script for the
  administration interface.
- ``bin/manage-report`` runs the Django ``manage.py`` script for the report
  interface.

Starting development Django web servers
---------------------------------------

Django's ``manage.py`` script has a ``runserver`` subcommand for running
development web servers. Run ``bin/manage-admin runserver 0:8000`` to start the
administration interface on port 8000, and ``bin/manage-report runserver
0:8001`` to start the report interface on port 8001. 

Starting the pipeline
---------------------

In a terminal
^^^^^^^^^^^^^

The five stages of the pipeline are normal Python programs, implemented by five
modules in the ``src/os2datascanner/engine2/pipeline/`` directory. Start them
with the following commands:

  - ``bin/pex python -m os2datascanner.engine2.pipeline.explorer``
  - ``bin/pex python -m os2datascanner.engine2.pipeline.processor``
  - ``bin/pex python -m os2datascanner.engine2.pipeline.matcher``
  - ``bin/pex python -m os2datascanner.engine2.pipeline.tagger``
  - ``bin/pex python -m os2datascanner.engine2.pipeline.exporter``

Note that these commands will remain in the foreground to print status
information.

With ``systemd``
^^^^^^^^^^^^^^^^

The ``contrib/systemd/`` folder contains ``systemd`` unit templates for the
pipeline stages. These templates also include some isolation settings which run
the pipeline stages as unprivileged users and prevent them from modifying the
local filesystem.

Copy these files into the ``/etc/systemd/system/`` directory, run ``systemd
daemon-reload`` to inform ``systemd`` about them, and then start the stages
with the following command:

  ``systemctl start os2ds-explorer@0.service os2ds-processor@0.service
  os2ds-matcher@0.service os2ds-tagger@0.service os2ds-exporter@0.service``

It's also possible to use these unit templates to start multiple instances of,
for example, the processor stage:

  ``systemctl start os2ds-processor@1.service os2ds-processor@2.service
  os2ds-processor@3.service``

``systemd`` subcommands also support wildcards, which can be used to get an
overview of the entire pipeline at once:

  ``systemctl status os2ds-*.service``

Starting the collector
----------------------

The report module has a separate component, the *pipeline collector*, that
reads results from the pipeline and inserts them into its database. This is
exposed as a Django management command through the ``bin/manage-report``
script:

  ``bin/manage-report pipeline_collector``

Run this command (which, again, will remain in the foreground) to make pipeline
results available to the report interface.

Using the system
==================

Creating a Django user
----------------------

The Django apps use Django's normal access control mechanisms. To create a user
with full privileges, use the ``createsuperuser`` command for each app:

  - ``bin/manage-admin createsuperuser``
  - ``bin/manage-report createsuperuser``

The ``createsuperuser`` command will prompt for a username, an email address,
and a password for the new accounts.

(Once a superuser account has been created, it can be used in the Django
administration interface to create accounts with more granular permissions.)

Logging in to the system
------------------------

The administration interface can be found at ``http://localhost:8000``.
