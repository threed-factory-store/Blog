#!/home/walt/bin/python

from wsgiref.handlers import CGIHandler
from app import app as application          # MUST be called application
import sys
sys.path.insert(0, '/home/walt/Documents/Blog')

CGIHandler().run(application)