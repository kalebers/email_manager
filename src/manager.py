import imaplib
import smtplib
import email
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header

# Connect to the IMAP server
def connect_imap(server, email, password):
    mail = imaplib.IMAP4_SSL(server)
    mail.login(email, password)
    return mail

# Connect to the SMTP server
def connect_smtp(server, port, email, password):
    smtp = smtplib.SMTP_SSL(server, port)
    smtp.login(email, password)
    return smtp

# Fetch emails from the specified folder
def fetch_emails(mail, folder='inbox'):
    mail.select(folder)
    result, data = mail.search(None, 'ALL')
    email_ids = data[0].split()
    emails = []

    for eid in email_ids:
        result, msg_data = mail.fetch(eid, '(RFC822)')
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Decode the email subject
        subject, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8')
        
        # Extract the email body
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()

        emails.append({
            'subject': subject,
            'body': body,
            'from': msg.get('From')
        })

    return emails

# Send an email
def send_email(smtp, from_email, to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    smtp.sendmail(from_email, to_email, msg.as_string())

# Automated responses to common queries
def auto_respond(smtp, emails, from_email):
    for email in emails:
        if 'common query' in email['body'].lower():
            response = "Thank you for your query. Here is the information you requested..."
            send_email(smtp, from_email, email['from'], 'Re: ' + email['subject'], response)

# Extract unsubscribe links from emails
def unsubscribe_from_spam(emails):
    unsubscribe_links = []
    for email in emails:
        if 'newsletter' in email['subject'].lower() or 'unsubscribe' in email['body'].lower():
            # Look for unsubscribe link in the email body
            links = re.findall(r'(https?://\S+)', email['body'])
            for link in links:
                if 'unsubscribe' in link:
                    unsubscribe_links.append(link)
    
    return unsubscribe_links

# Main function to manage emails
def manage_emails(imap_server, smtp_server, smtp_port, email_user, email_pass):
    imap_conn = connect_imap(imap_server, email_user, email_pass)
    smtp_conn = connect_smtp(smtp_server, smtp_port, email_user, email_pass)

    emails = fetch_emails(imap_conn)
    for email in emails:
        print(email['subject'], email['from'])
    
    auto_respond(smtp_conn, emails, email_user)
    
    unsubscribe_links = unsubscribe_from_spam(emails)
    for link in unsubscribe_links:
        print("Unsubscribe link:", link)

    # Close the connections
    imap_conn.logout()
    smtp_conn.quit()

# Example usage
if __name__ == "__main__":
    imap_server = 'imap.gmail.com'
    smtp_server = 'smtp.gmail.com'
    smtp_port = 465
    email_user = 'your_email@gmail.com'
    email_pass = 'your_password'

    manage_emails(imap_server, smtp_server, smtp_port, email_user, email_pass)
