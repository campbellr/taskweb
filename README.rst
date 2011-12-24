========
Task Web
========

``task web`` is a Django-based web front-end for `taskwarrior <http://taskwarrior.org>`_.

Although it currently very much in it's infancy, the project is intended to allow
users to host a taskwarrior database for syncing with ``task merge``, as well as adding,
editing, and closing tasks through the web.

.. note::
   ``task web`` is not yet in a usable state.

.. image:: http://github.com/campbellr/taskweb/raw/master/taskweb.png
    :align: right
    :alt: taskweb screenshot

Installation
=============

``task web`` isn't yet available on pypi, but can be installed using ``setup.py install``::

 $ [sudo] python setup.py install

You can then configure it like any other django project (customize ``settings.py``, set up
http server, etc...).


Requirements
============

``task web`` requires the following software:

    * `Django <http://djangoproject.com/>`_
    * `django-tables2 <https://github.com/bradleyayers/django-tables2>`_
    * `taskw <https://github.com/ralphbean/taskw>`_


TODO
====

 * Add ability to upload (and use) a taskwarrior DB
 * Add ability to edit tasks
 * Add ability to mark tasks 'done'
 * Expose uploaded db to a url for syncing with taskwarrior (``task pull``, ``task merge``)
 * Add calendar view, and other useful taskwarrior charts


Reporting Bugs
==============

Any bugs can be reported on the github `issue tracker <https://github.com/campbellr/taskweb/issues/new>`_.
