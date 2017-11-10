from openquake.moon import Moon
import atexit

import sys, os, time
import threading
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer

PUBLIC_DIRECTORY = os.path.join(os.path.dirname(__file__), 'webpages')

class MyRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        print("PATH: [%s]" % path)
        if path == '/':
            return PUBLIC_DIRECTORY + os.sep + 'index.html'
        else:
            return PUBLIC_DIRECTORY + os.sep.join(path.split('/'))

_httpserver = None
_httpserver_thread = None

pla = Moon()
pla.primary_set()

def setup_package():
    global _httpserver, _httpserver_thread
    _httpserver = HTTPServer(('', 8008), MyRequestHandler)
    _httpserver_thread = threading.Thread(target = _httpserver.serve_forever)
    _httpserver_thread.daemon = True
    try:
        _httpserver_thread.start()
    except KeyboardInterrupt:
        _httpserver_thread.shutdown()
        sys.exit(0)
    for i in range(1,1000):
        if _httpserver_thread.is_alive():
            break
        time.sleep(0.2)
        continue
            
    pla.init(landing="/index.html", autologin=False)

# turned off because nose run it at the wrong time
#def teardown_package():
#    print("teardown_package here")
#    pla.fini()

def my_at_exit():
    _httpserver.shutdown()
    _httpserver_thread.join(5)
    pla.fini()

atexit.register(my_at_exit)

