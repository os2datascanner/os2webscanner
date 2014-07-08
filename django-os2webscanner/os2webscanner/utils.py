from django.conf import settings
from django.core.mail import EmailMessage
from django.template import loader, Context


def notify_user(scan):
    """Notify user about completed scan - including success and failure."""
    template = 'os2webscanner/email/scan_report.html'

    t = loader.get_template(template)

    c = Context({'scan': scan, 'domain': settings.SITE_URL})

    subject = "Scanning afsluttet: {0}".format(scan.status_text)
    to_address = scan.scanner.organization.contact_email
    if not to_address:
        to_address = settings.ADMIN_EMAIL

    try:
        body = t.render(c)
        message = EmailMessage(subject, body, settings.ADMIN_EMAIL,
                               [to_address])
        message.send()
    except Exception as e:
        # TODO: Handle this properly
        raise
