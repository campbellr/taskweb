====================
Task Web (abandoned)
====================

Notice
======

Due to lack of time and bad design choices, this project is abandoned, although I do plan on
reviving it in some form once `taskd <http://tasktools.org/projects/taskd.html>`_ is released.

.. image:: https://secure.travis-ci.org/campbellr/taskweb.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/campbellr/taskweb

``task web`` is a Django-based web front-end for `taskwarrior <http://taskwarrior.org>`_.

Although it currently very much in it's infancy, the project is intended to allow
users to host a taskwarrior database for syncing with ``task merge``, as well as adding,
editing, and closing tasks through the web.

**NOTE**: ``task web`` is not yet in a usable state and **WILL CORRUPT YOUR TASK DATA** 
Make sure you have backups before testing the the task sync feature.

Screenshot
==========

.. image:: http://github.com/campbellr/taskweb/raw/master/taskweb.png
    :alt: taskweb screenshot

Installation
=============

``task web`` isn't yet available on pypi, and ``setup.py`` doesn't work quite yet, but if you
are willing to put up with a lot of bugs, just ``git pull`` and configure it like any other 
django project (customize ``settings.py``, set up http server, etc...).


Requirements
============

``task web`` requires the following software:

* `Django <http://djangoproject.com/>`_
* `djblets datagrid <https://github.com/djblets/djblets>`_
* `taskw <https://github.com/ralphbean/taskw>`_

TODO
====

* Add calendar view, and other useful taskwarrior charts/stats
* Better multi-user support
* Better tablet/mobile support
* Lots of usability enhancements

Reporting Bugs
==============

Any bugs can be reported on the github `issue tracker <https://github.com/campbellr/taskweb/issues/new>`_.
