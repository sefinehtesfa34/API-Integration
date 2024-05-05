import sys
import os

# Assuming your Flask app is named 'app.py' and it's in the same directory as 'app.wsgi'
sys.path.insert(0, '/projects/flask_app')
os.environ['FLASK_APP'] = 'app.py'

from app import app as application  # Import the Flask app