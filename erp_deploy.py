"""Gunicorn *development* config file"""

# Django WSGI application path in pattern MODULE_NAME:VARIABLE_NAME
wsgi_app = "core.wsgi:application"
# The granularity of Error log outputs
loglevel = "debug"
# The number of worker processes for handling requests
workers = 3
# The socket to bind
bind = "0.0.0.0:9090"
# Restart workers when code changes (development only!)
# reload = True
# Write access and error info to /var/log
# errorlog = "/var/log/gunicorn/mini_erp.log"
# Redirect stdout/stderr to log file
capture_output = True
# PID file so you can easily fetch process ID
pidfile = "mini_erp.pid"
# Daemonize the Gunicorn process (detach & enter background)
daemon = True