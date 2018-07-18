import unittest

from exchangelib import IMPERSONATION, ServiceAccount, Account


class ExchangeScannerTest(unittest.TestCase):

    def exchange_login_test(self):
        credentials = ServiceAccount(username='',
                                     password='')
        username = ''
        self.account = Account(primary_smtp_address=username,
                               credentials=credentials, autodiscover=True,
                               access_type=IMPERSONATION)
        self.account.root.refresh()


def main():
    """Run the unit tests."""
    unittest.main()


if __name__ == '__main__':
    main()