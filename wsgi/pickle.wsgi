#!/usr/bin/python

import os
import sys
import cgi
from subprocess import call
sys.path.append('/var/www/wsgi-scripts')
os.environ['PYTHON_EGG_CACHE'] = '/var/www/.python-egg'

is_running = False
cmd_file = '/var/www/bin/pickle_ctl.sh'
cmd_output = '/tmp/cmd_output'
cmd_status = '/tmp/cmd_status'
data_dir = '/var/www/data'

def check_service():
    with open(cmd_status, 'w') as f:
        rc = call([cmd_file,"status"],stdout=f, stderr=f)
        if rc == 0:
            return True
        else:
            return False

def application(environ, start_response):
    global is_running
    is_running = check_service()
    # get the elements
    form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    if 'toggle' in form.keys():
        result = cmd_app()
        print >> environ['wsgi.errors'], '%s: %s' % ('ToggleResult', result)
        is_running = check_service()
    return say_app(environ, start_response, full_page())

def full_page():
    return page_top + form() + file_list() + page_bottom

def cmd_app():
    with open(cmd_output, 'w') as f:
        rc = 0
        if is_running:
            rc = call([cmd_file,"stop"],stdout=f, stderr=f)
        else:
            rc = call([cmd_file,"start"],stdout=f, stderr=f)
        if rc == 0:
            return ('SUCCESS')
        else:
            return ('FAILED')

def say_app(environ, start_response, say):
   #print >> environ['wsgi.errors'], 'WSGI OK: %s' % say
   headers = [('content-type', 'text/html')]
   start_response('200 OK', headers)
   return [say]

page_top = """
    <html><head>
    <title>PickleTown</title>
    <meta http-equiv="refresh" content="15;URL='/pickle'" /> 
    <style>
    form {
      /* Just to center the form on the page */
      margin: 0 auto;
      width: 400px;
      /* To see the outline of the form */
      padding: 1em;
      border: 1px solid #CCC;
      border-radius: 1em;
    }
    input:focus, textarea:focus {
      /* To give a little highlight on active elements */
      border-color: #000;
    }
    </style>
    </head><body>
    <h1 style="color:blue;text-align:center">Pickle Data Collection</h1>
    <p style="color:blue;text-align:center">You can toggle the data collector with the button. Currently, collection is:</p>
    """

def form():
    if is_running:
        status = '<p style="color:green;text-align:center">RUNNING</p>'
    else:
        status = '<p style="color:red;text-align:center">STOPPED</p>'
    form = """
    <form method="post">
    <input type="hidden" name="toggle" value="yes">
    <button type="submit" style="text-align:center">Start/Stop</button>
    </form>
    """
    return status + form

def file_list():
    flist = ''
    files = os.listdir(data_dir)
    for f in files:
        flist.append('<a href="/data/' + f + '">' + f + '</a><br />')
    return flist

page_bottom = '</body></html>'

page_404 = """<html>
<h1>Page not Found</h1>
<p>That page is unknown. Return to the <a href="/">home page</a></p>
</html>
"""
def show_404_page(environ, start_response):
#    """An application that always returns a 404 response"""
    headers = [('content-type', 'text/html')]
    start_response('404 Not Found', headers)
    return [page_404.encode(),]
