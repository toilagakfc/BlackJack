import os

DEBUG = os.getenv('DEBUG', 'False') == 'True'
PORT = int(os.getenv('PORT', '8000'))
