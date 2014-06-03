======================
Installation and setup
======================

.. contents:: :backlinks: none

Assuming fresh Linux Ubuntu/Debian (Ubuntu 13.10) installed.

Install
=======

1. Python 3, Apache 2 and its WSGI module for Python 3

  .. code-block:: console

      $ sudo apt-get install python3
      $ sudo apt-get install apache2
      $ sudo apt-get install libapache2-mod-wsgi-py3

2. PostgreSQL 9

      $ sudo apt-get install postgresql
      $ sudo apt-get install postgresql-contrib

3. git and pip

  .. code-block:: console

      $ sudo apt-get install git
      $ cd /tmp
      $ sudo wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
      $ sudo python3 get-pip.py

4. Django and other Python libraries

  .. code-block:: console

      $ pip install django
      $ sudo apt-get build-dep python-psycopg2
      $ pip install psycopg2
      $ pip install djorm-ext-pgfulltext
      $ pip install requests

5. zex

  .. code-block:: console

      $ cd /var/www
      $ sudo git clone https://github.com/girogiro/zex.git
      $ chmod o+w zex/zex/static/zex/js

Setup database
==============

  .. code-block:: console

      $ sudo service postgresql start
      $ sudo su - postgres
      $ psql -f init_db.sql
      $ logout
      $ cd /var/www/zex
      $ python3 manage.py syncdb

Configure Apache (2.4)
======================

Add the following line to ``/etc/apache2/ports.conf``:

::

Listen 8080

and create file ``/etc/apache2/sites-available/zex.conf`` with content:

::

    <VirtualHost *:8080>
    #    ServerName zex

        ErrorLog ${APACHE_LOG_DIR}/zex/error.log
        CustomLog ${APACHE_LOG_DIR}/zex/access.log combined

        <Directory /var/www/zex/>
            Require all granted
            AllowOverride None
            Order allow,deny
            Allow from all
        </Directory>

        WSGIDaemonProcess zex_process python-path=/var/www/zex:
        WSGIScriptAlias / /var/www/zex/project/wsgi.py
        WSGIProcessGroup zex_process
        WSGIApplicationGroup %{GLOBAL}

        AliasMatch ^/([^/]*\.css) /var/www/zex/zex/static/zex/css/$1
        AliasMatch ^/([^/]*\.js) /var/www/zex/zex/static/zex/js/$1
        Alias /media/ /var/www/zex/zex/media/
        Alias /static/ /var/www/zex/zex/static/

        <Directory /var/www/zex/zex/media>
            Require all granted
        </Directory>

        <Directory /var/www/zex/zex/static>
            Require all granted
        </Directory>
    </VirtualHost>
	
Then

.. code-block:: console

    $ sudo mkdir /var/log/apache2/zex
    $ sudo a2ensite zex
    $ sudo service apache2 reload

Test
====

Visit

::

    http://<ip-or-domain>:8080/zex

It should work.

Load data
=========

Visit

::

    http://<ip-or-domain>:8080/zex/update

and again

::

    http://<ip-or-domain>:8080/zex
