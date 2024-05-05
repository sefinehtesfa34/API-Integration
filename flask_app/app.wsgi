#!/usr/bin/python3
import sys
import site
from os.path import abspath, dirname, join

# Calculate path to site-packages directory.
python_home = '/var/www/API-Integration/flask_app/venv'
site_packages = join(python_home, 'lib', 'python3.12', 'site-packages')

# Add the site-packages directory.
site.addsitedir(site_packages)

sys.path.insert(0, '/var/www/API-Integration/flask_app')

from app import app as application  # Import the application