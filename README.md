echo - a python wsgi test
=========================
I wrote this in late 2011 to test wsgi implementations. I couldn't believe it, but i needed something like this. Code is not good, but the number of edge cases I had to work around is.

Original notebook line:
> test in-app wsgi servers - cherrypy, twisted, tornado (fail to install gevent, fapws3) from http://nichol.as/benchmark-of-python-web-servers

Usage
-----

* `virtualenv -p /usr/bin/python2 venv`
* `venv/bin/pip install -r requirements.txt`
* `venv/bin/python echo.py localhost 8001 eventlet` or one of `wsgiref`, `eventlet`, `cherrypy`, `twisted`, and `tornado`

License
-------

MIT. it's a single file, it really doesn't matter.


