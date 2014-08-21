from getpass import getpass

from webscanner_client import WebscannerClient

# Change this to the actual URL you want to test against.
TEST_URL = 'http://localhost:8080'
# Relative URL of XML-RPC service - change if server setup is non-default.
XMLRPC_URL = '/xmlrpc/'

wc = WebscannerClient(TEST_URL + XMLRPC_URL)

username = "agger" #raw_input('User name: ')

password = "agger" # getpass()

url = "http://www.magenta.dk" #raw_input('Enter URL: ')

#wc.scan_urls(username, password, [url])

wc.scan_documents(username, password, ['/etc/passwd'])
