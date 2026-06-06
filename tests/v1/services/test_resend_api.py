import os
import resend
from dotenv import load_dotenv

load_dotenv()
# RESEND_API_KEY environment variable
resend.api_key = os.environ.get("RESEND_API_KEY")


try:
    email = resend.Emails.send(
        {
            "from": "hello@erdisonmalko.com",
            "to": "sonimailfortestuse@gmail.com",
            "subject": "Testing Custom Domain",
            "html": "<strong>It works perfectly!</strong>",
        }
    )
    print(f"Email sent successfully! Message ID: {email['id']}")

except Exception as e:
    print(f"Failed to send email: {e}")
