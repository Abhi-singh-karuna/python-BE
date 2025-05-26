from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class EmailService:
    def __init__(self, api_key, from_email, from_name):
        self.sg = SendGridAPIClient(api_key)
        self.from_email = from_email
        self.from_name = from_name

    def send_email(self, to_email, subject, body):
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=body
        )
        response = self.sg.send(message)
        return response 