import os
from dotenv import load_dotenv

load_dotenv()

import requests

headers = {
    "Authorization": f"Bearer {os.getenv('RAILWAY_TOKEN')}",
    "Content-Type": "application/json",
}

query = """
{
  me {
    id
    email
  }
}
"""

response = requests.post(
    "https://backboard.railway.app/graphql/v2",  # updated URL
    json={"query": query},
    headers=headers,
)
print(response.status_code)
print(response.text)
