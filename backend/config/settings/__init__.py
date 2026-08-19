import os
from pathlib import Path
from dotenv import load_dotenv

# Points to the absolute root directory of your Django project backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read the local configuration profile
if (BASE_DIR / '.env').exists():
    load_dotenv(BASE_DIR / '.env')
else:
    load_dotenv(BASE_DIR.parent / '.env')

# Import your configurations safely
from .base import *
