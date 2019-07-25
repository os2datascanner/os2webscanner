import structlog
from exchangelib import IMPERSONATION, ServiceAccount, Account, Configuration
from exchangelib.errors import ErrorNonExistentMailbox

logger = structlog.get_logger()


class ExchangeServerAssistant(object):
    """
    ExchangeServer class holds information needed to get access
    and download content from an Exchange Server Account.

    The service_endpoint for Office365 is default
    'https://outlook.office365.com/EWS/Exchange.asmx'
    """

    service_endpoint = 'https://outlook.office365.com/EWS/Exchange.asmx'

    def __init__(self, credentials,
                 user_name, export_path,
                 mail_ending, start_date=None,
                 is_office365=False):
        """
        Initializes an ExchangeServer object.
        The only difference between Exchange Server and Office365
        is that an endpoint is needed and we cannot use autodiscover
        (at least to our knowledge).

        :param credentials: Service Account Credentials
        :param user_name: Username for Exchange Account
        :param export_path: Download path
        :param mail_ending: The Email domain
        :param start_date: Date from when we should download mails from
        :param is_office365: Is the Exchange Server an Office365 instance or not
        """


        self.credentials = credentials
        self.user_name = user_name
        self.export_path = export_path
        self.mail_ending = mail_ending
        self.start_date = start_date
        self.is_office365 = is_office365

    def get_user_email_address(self):
        return self.user_name + self.mail_ending

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
        """
        Getter for retreiving an Exchange Account object.
        The account object is the account for the mailbox user
        you want to download mails from.

        :return: returns an exchange account object
        """
        service_account = self.get_service_account()
        account = None
        config = None
        if self.is_office365:
            config = Configuration(service_endpoint=self.service_endpoint,
                                   credentials=service_account)
        try:
            account = Account(primary_smtp_address=self.get_user_email_address(),
                              credentials=service_account,
                              config=config,
                              autodiscover=False if self.is_office365 else True,
                              access_type=IMPERSONATION)
            account.root.refresh()
            logger.info('{}: Init complete'.format(self.username))
        except ErrorNonExistentMailbox:
            logger.error('No such user: {}'.format(self.username))

        return account