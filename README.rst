Create beautifully parsed HTML logs from boring text files, using this simple tool

====================
Installation & Setup
====================

------
Docker
------

  - Actually have docker installed and running (ie. ``docker ps`` works)
  - Rename ``docker-compose.env.example`` to ``docker-compose.env``
  - Provide a Discord Bot token in ``docker-compose.env``
  - ``docker-compose build``
  - ``docker-compose up``
  - Go to ``localhost:80`` in a browser

--------
Manually
--------

  - god help you
  - Install Python 3.7 (or 3.6), Postgres, Redis
  - Setup Postgres and Redis
  - Follow the install instruction for Psycopg here: http://initd.org/psycopg/docs/install.html
  - Run ``pip install -r ./requirements.txt``
  - Run ``python setup.py install``
  - Setup all the env vars from ``docker-compose.env``
  - Run ``python manage.py migrate``
  - Run ``python manage.py runserver 0.0.0.0:80``
  - Go to ``localhost:80`` in a browser
  - Realize using docker would've done all of this for you
