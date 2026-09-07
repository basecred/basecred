"""
Vercel Serverless Entrypoint for BaseCred.
Routes all /api/* requests to the BaseCredHandler.
"""
import os
import sys

# Ensure root directory is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server import BaseCredHandler

# Vercel serverless function entrypoint
class handler(BaseCredHandler):
    pass
