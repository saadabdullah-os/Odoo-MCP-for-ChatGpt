import os
import sys

# Ensure parent directory is on sys.path so main.py is importable by Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
