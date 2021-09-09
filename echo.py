#!/usr/bin/env python

"""
echo - run as py script, or wsgi runner, pretty flexible. Echos input to output.
I wish I commented this better.
2011 Paul Oppenheim <hack@pauloppenheim.com>
"""

import os
import sys
import locale
import re
import pprint
import Cookie
import cgi

import StringIO

import select


def application(environ, start_response):
    sys.stdout = environ['wsgi.errors']
    
    http_code = "200 OK"
    http_headers = [('content-type', 'text/plain; charset=utf-8')]
    result = ""
    
    default_encoding = "utf-8"
    enctype = "default"
    if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
        default_encoding = sys.stdout.encoding
        enctype = "sys"
    else:
        default_encoding = locale.getpreferredencoding()
        enctype = "locale"
    result += "\n encoding: %s source: %s \n" % (default_encoding, enctype)
    
    result += "\n"
    result += " HEADERS "
    result += '--------------------------------------------------------------------------------'
    result += "\n"
    e = []
    for k in environ:
        e.append(k)
    e.sort()
    #for k in e:
    #    print(k + ": " + pprint.pformat(os.environ[k], 4, 40))
    #print
    for k in e:
        result += (k + ": " + pprint.pformat(environ[k], 4, 40)) + "\n"
        #if re.compile("^HTTP_|QUERY_|REQUEST_").match(k):
        #    print(k + ": " + pprint.pformat(os.environ[k], 4, 40))
    
    if environ.has_key('HTTP_COOKIE'):
        result += "\n"
        result += " COOKIES "
        result += '--------------------------------------------------------------------------------'
        result += "\n"
        c = Cookie.BaseCookie(environ['HTTP_COOKIE'])
        result += c.output()
    
    """
    # simple-style forms - no raw data access
    form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    if form is not None:
        result += "\n"
        result += " FORM DATA - CGI PARSED "
        result += '--------------------------------------------------------------------------------'
        result += "\n"
        result += pprint.pformat(form)
    """
    
    # complex-style forms - raw data access
    if environ.has_key('CONTENT_TYPE'):
        content_type_header = environ['CONTENT_TYPE']
    else:
        content_type_header = None
    
    if content_type_header:
        ctype, pdict = cgi.parse_header(content_type_header)
    else:
        ctype, pdict = None, None
    
    if ctype == 'multipart/form-data':
        postdata_f = StringIO.StringIO(environ['wsgi.input'].read())
        postdata = postdata_f.getvalue()
        postvars = cgi.parse_multipart(postdata_f, pdict)
    elif ctype == 'application/x-www-form-urlencoded':
        length = int(environ['CONTENT_LENGTH'])
        #postvars = cgi.parse_qs(environ['wsgi.input'].read(length), keep_blank_values=1)
        postdata = environ['wsgi.input'].read(length)
        postvars = cgi.parse_qs(postdata, keep_blank_values=1)
    else:
        ioh = environ['wsgi.input']
        rlist, wlist, xlist = [], [], []
        def a():
            pass
        if isinstance(getattr(ioh, 'fileno', None), type(a)):
            rlist, wlist, xlist = select.select([ioh], [], [])
        
        if len(rlist) > 0:
            postdata_f = StringIO.StringIO(environ['wsgi.input'].read())
            postdata = postdata_f.getvalue()
        else:
            postdata = None
        postvars = None
    
    if postvars is not None or postdata is not None:
        result += "\n"
        result += " FORM DATA - CGI SPLIT, UNPARSED / PARSED (from %s)\n" % ctype
        result += '--------------------------------------------------------------------------------'
        result += "\n"
        result += "\n"
        result += pprint.pformat(postdata)
        result += "\n"
        result += "\n"
        result += pprint.pformat(postvars)
        #result += "\n"
        #d = StringIO.StringIO(postdata)
        #result += pprint.pformat(d.readlines())
    
    """
    result += "\n"
    result += " PATH "
    result += '--------------------------------------------------------------------------------'
    result += "\n"
    for d in sys.path:
        result += str(d) + "\n"
    result += "\n"
    """
    
    # Avoid manhandling input - can't use it later if you do
    result += "\n"
    result += " INPUT "
    result += '--------------------------------------------------------------------------------'
    result += "\n'''\n"
    #for line in environ['wsgi.input']:
    #    result += line + "\n"
    for line in iter(environ['wsgi.input'].readline, ''):
        result += line + "\n"
    result += "'''\n"
    
    start_response(http_code, http_headers)
    return (result,)



def do_wsgiref(addr):
    print "using wsgiref"
    import wsgiref.simple_server
    httpd = wsgiref.simple_server.make_server(addr[0], addr[1], application)
    httpd.serve_forever()

def do_eventlet(addr):
    print "using eventlet"
    import eventlet
    import eventlet.wsgi
    eventlet.monkey_patch()
    eventlet.wsgi.server(eventlet.listen(addr, backlog = 20000), application)

def do_cherrypy(addr):
    print "using cherrypy"
    import cherrypy.wsgiserver
    #cherrypy.config.update({'log.screen': True})
    server = cherrypy.wsgiserver.CherryPyWSGIServer(
        addr,
        application,
        server_name='www.cherrypy.example',
        request_queue_size=500)
    try: # if you don't have this try-catch, Ctrl-C doesn't always stop the server
        server.start()
    except KeyboardInterrupt:
        server.stop()

def do_twisted(addr):
    print "using twisted"
    import twisted.web.wsgi
    import twisted.web.server
    import twisted.internet.reactor
    resource = twisted.web.wsgi.WSGIResource(twisted.internet.reactor, twisted.internet.reactor.getThreadPool(), application)
    site = twisted.web.server.Site(resource)
    twisted.internet.reactor.listenTCP(addr[1], site)
    twisted.internet.reactor.run()

def do_tornado(addr):
    print "using tornado"
    import tornado.httpserver
    import tornado.ioloop
    import tornado.wsgi
    container = tornado.wsgi.WSGIContainer(application)
    server = tornado.httpserver.HTTPServer(container)
    # http://www.tornadoweb.org/documentation/httpserver.html
    
    # method 1 - listen
    #http_server.listen(addr[1])
    
    #method 2 - multi-process
    server.bind(addr[1])
    server.start(100)  # Forks multiple sub-processes
    
    tornado.ioloop.IOLoop.instance().start()

def main():
    #def a(x, y):
    #    print x
    #    print y
    #x = application({'wsgi.input': sys.stdin}, a)
    #print x
    
    server_address = sys.argv[1]
    server_port = int(sys.argv[2])
    addr = (server_address, server_port)
    print "Serving on port %s..." % server_port
    server_type = "wsgiref"
    if 3 < len(sys.argv):
        server_type = sys.argv[3]
    
    handlers = {
        "wsgiref": do_wsgiref,
        "eventlet": do_eventlet,
        "cherrypy": do_cherrypy,
        "twisted": do_twisted,
        "tornado": do_tornado,
    }
    handlers[server_type](addr)
    #return i guess?

if __name__ == "__main__":
    main()
