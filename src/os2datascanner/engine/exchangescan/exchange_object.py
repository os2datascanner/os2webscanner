import structlog
from exchangelib import IMPERSONATION, ServiceAccount, Account, Configuration
from exchangelib.errors import ErrorNonExistentMailbox

logger = structlog.get_logger()


class ExchangeServer(object):
    """
    ExchangeServer class holds information needed to get access
    and download content from an Exchange Server Account.
    """
    def __init__(self, credentials,
                 user_name, export_path,
                 mail_ending, start_date):
        self.credentials = credentials
        self.user_name = user_name
        self.export_path = export_path
        self.mail_ending = mail_ending
        self.start_date = start_date


    def get_service_account(self):
        """
        Getter for retreiving an Exchange Service Account object.
        A Service Account is used by the service to act on behalf
        of the user accounts.
        :return: An Exchange Service Account object
        """
        return ServiceAccount(username=self.credentials[0],
                              password=self.credentials[1])

    def get_account(self):
        account = None
        try:
            account = Account(primary_smtp_address=self.username,
                              credentials=self.get_service_account(),
                              autodiscover=True,
                              access_type=IMPERSONATION)
            account.root.refresh()
            logger.info('{}: Init complete'.format(self.username))
        except ErrorNonExistentMailbox:
            logger.error('No such user: {}'.format(self.username))

        return account


class Office365(ExchangeServer):
    def __init__(self, service_endpoint =
    'https://outlook.office365.com/EWS/Exchange.asmx'):
        """
        Initializes an Office365 object.
        The only difference between Exchange Server and Office365
        is that an endpoint is needed.

        :param service_endpoint:
        service_endpoint for office365 is default
        'https://outlook.office365.com/EWS/Exchange.asmx'
        """
        self.service_endpoint = service_endpoint

    def get_account(self):
        """
        Getter for retreiving an Exchange Account object.
        The account object is the account for the mailbox user
        you want to download mails from.

        :return: returns an exchange account object
        """
        service_account = self.get_service_account()
        config = Configuration(service_endpoint=self.service_endpoint,
                               credentials=service_account)
        account = None
        try:
            account = Account(primary_smtp_address=self.user_name,
                              credentials=service_account,
                              config=config,
                              autodiscover=False,
                              access_type=IMPERSONATION)
            account.root.refresh()
            logger.info('{}: Init complete'.format(self.username))
        except ErrorNonExistentMailbox:
            logger.error('No such user: {}'.format(self.username))

        return account