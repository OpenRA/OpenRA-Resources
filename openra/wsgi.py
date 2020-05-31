"""
WSGI config for openra project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os
import logging
import sys
from django.core.wsgi import get_wsgi_application


logging.basicConfig(stream=sys.stderr)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


sys.path.append(BASE_DIR)
os.chdir(BASE_DIR)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openra.settings")

application = get_wsgi_application()
