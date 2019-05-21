====================
Logging with Graylog
====================

OS2datascanner supports logging to Graylog. This directory contains a
simple ``docker-compose`` file derived from `their documentation
<https://docs.graylog.org/en/3.0/pages/installation/docker.html>`_.

.. warning:: The configuration of this installation is *woefully*
             insecure; **DO NOT USE IT IN PRODUCTION!**

In order to deploy this installation, you first have to `install
<https://docs.docker.com/compose/install/>`_ ``docker-compose``. Then,
run ``docker-compose up`` from within this directory. After
downloading the relevant packs and starting Mongo, ElasticSearch and
Graylog, that'll give you an instance of Graylog running on
`<http://localhost:9000>`_.

To set this instance up for receiving logging, login as
``admin``/``admin``, go to *Inputs*, and add a new *GELF UDP* input
using the default settings. We also support TCP and AMQP, but UDP is
Good Enough™

Then, set the environemnt variable ``DJANGO_GRAYLOG_HOST`` to
``localhost`` when running the various scanning processes.
