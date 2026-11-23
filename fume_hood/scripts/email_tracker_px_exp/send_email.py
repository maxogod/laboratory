import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys


def send_email(addr: str):
    GMAIL_USER = "<email>"
    GMAIL_APP_PASSWORD = "<pw>"

    TO_EMAIL = addr
    SUBJECT = "Atus"

    HTML_BODY = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            .container { padding: 20px; background-color: #f4f4f4; }
            .content { background: white; padding: 20px; border-radius: 5px; box-shadow: 0px 0px 10px #ccc; }
            h1 { color: #333; }
            p { font-size: 16px; }
            .footer { margin-top: 20px; font-size: 12px; color: #555; }
        </style>
    </head>
    <body>
    <h1>Hiii atusss</h1>
    <img width="1px" height="1px" src="http://181.169.31.52:3000/px.jpg" style="display:none;" />
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = SUBJECT
    msg.attach(MIMEText(HTML_BODY, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)


if __name__ == "__main__":
    print("sending email")
    if len(sys.argv) < 2:
        print("Usage: python3 send_email.py email")
        sys.exit(1)

    addr = sys.argv[1]
    send_email(addr)
