import os
from dotenv import load_dotenv

load_dotenv()

from urllib.parse import quote_plus

print(quote_plus(os.getenv("DATABASE_PASSWORD")))
