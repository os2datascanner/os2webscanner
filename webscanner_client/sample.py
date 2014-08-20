from getpass import getpass

from webscanner_client import WebscannerClient

# Change this to the actual URL you want to test against.
TEST_URL = 'http://localhost:8080'
# Relative URL of XML-RPC service - change if server setup is non-default.
XMLRPC_URL = '/xmlrpc/'

wc = WebscannerClient(TEST_URL + XMLRPC_URL)

username = raw_input('User name: ')

password = getpass()

url = raw_input('Enter URL: ')

wc.scan_urls(username, password, [url])

# TODO: Write sample document scanning too.
