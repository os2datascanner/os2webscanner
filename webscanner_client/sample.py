"""Sample testing of the Python webscanner client."""
from getpass import getpass

from webscanner_client import WebscannerClient

# Change this to the actual URL you want to test against.
TEST_URL = 'http://localhost:8080'
# Relative URL of XML-RPC service - change if server setup is non-default.
XMLRPC_URL = '/xmlrpc/'

username = raw_input('User name: ')
password = getpass()

url = raw_input('Enter URL: ')

wc = WebscannerClient(TEST_URL + XMLRPC_URL)
report_url = wc.scan_urls(username, password, [url])
status = wc.get_status(username, password, report_url)

print "URL: {0}\nStatus: {1}".format(report_url, status[0])

filename = raw_input('Enter file name:')

report_url = wc.scan_documents(username, password, [filename])
status = wc.get_status(username, password, report_url)

print "URL: {0}\nStatus: {1}".format(report_url, status[0])

report = wc.get_report(username, password, report_url)

print report
