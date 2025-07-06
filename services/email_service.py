import resend
from flask import current_app as app

Resend_API_KEY = app.config['RESEND_API_KEY']
resend.api_key = Resend_API_KEY

r = resend.Emails.send({
  "from": "onboarding@resend.dev",
  "to": "eerie.boi.official@gmail.com",
  "subject": "Hello World",
  "html": "<p>Congrats on sending your <strong>first email</strong>!</p>"
})
