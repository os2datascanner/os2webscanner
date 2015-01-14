#!/usr/bin/env python

"""Sample testing of the Python webscanner client."""
from getpass import getpass
import time
import sys
import urlparse
import argparse

from webscanner_client import WebscannerClient

# Change this to the actual URL you want to test against.
WEBSCANNER_URL = 'http://localhost:8080'

# Relative URL of XML-RPC service - change if server setup is non-default.
XMLRPC_URL = '/xmlrpc/'

parser = argparse.ArgumentParser(description='Sample Webscanner RPC client')
parser.add_argument('FILE_OR_URL', help="The file or URL to scan")

parser.add_argument('-u', '--username', dest='username', help="Username",
                    required=True)


# Params arguments
parser.add_argument('-c', '--cpr', dest='do_cpr_scan', help="Do CPR scan",
                    action="store_true", default=False)

parser.add_argument('--cpr-mod11', dest='do_cpr_modulus11',
                    help="Do CPR modulus 11 check",
                    action="store_true", default=False)

parser.add_argument('--cpr-ignore-irrelevant',
                    dest='do_cpr_ignore_irrelevant',
                    help="Ignore irrelevant CPR birth dates",
                    action="store_true", default=False)

parser.add_argument('-n', '--name', help="Do name scan", dest='do_name_scan',
                    action="store_true", default=False)


parser.add_argument('-o', '--ocr', dest='do_ocr',
                    help="Do OCR scan", action="store_true",
                    default=False)


parser.add_argument('--output-spreadsheet', dest='output_spreadsheet_file',
                    help="Output spreadsheet file with annotations",
                    action="store_true", default=False)

parser.add_argument('--cpr-replace', dest='do_cpr_replace',
                    help="Replace CPRs",
                    action="store_true", default=False)
parser.add_argument('--cpr-replace-text', dest='cpr_replace_text',
                    help="CPR replacement text")

parser.add_argument('--name-replace', dest='do_name_replace',
                    help="Replace Names",
                    action="store_true", default=False)
parser.add_argument('--name-replace-text', dest='name_replace_text',
                    help="Name replacement text")


parser.add_argument('-W', dest='webscanner_url',
                    help="URL of the webscanner server",
                    default=WEBSCANNER_URL)

parser.add_argument('--output-file', dest='output_file',
                    help="Output results to a CSV file")

args = parser.parse_args()

if not (args.do_cpr_scan or args.do_name_scan):
    print "Must specify at least one type of scan (--cpr or --name)"
    sys.exit()

username = args.username
password = getpass()

params = {}


supported_params = ["do_cpr_scan", "do_cpr_modulus11",
                    "do_cpr_ignore_irrelevant", "do_ocr", "do_name_scan",
                    "output_spreadsheet_file", "do_cpr_replace",
                    "cpr_replace_text", "do_name_replace",
                    "name_replace_text", "do_address_replace",
                    "address_replace_text"]

# Copy the command options to the params dict
for param in supported_params:
    if param in args and getattr(args, param) is not None:
        params[param] = getattr(args, param)

print "Parameters:", params

wc = WebscannerClient(urlparse.urljoin(args.webscanner_url, XMLRPC_URL))

print "Running scan..."

if args.FILE_OR_URL.startswith('http://') or args.FILE_OR_URL.startswith(
        'https://'):
    url = args.FILE_OR_URL
    report_url = wc.scan_urls(username, password, [url], params)
else:
    filename = args.FILE_OR_URL
    report_url = wc.scan_documents(username, password, [filename], params)

status = wc.get_status(username, password, report_url)

spinner_chars = "/-\\|"
spinner_counter = 0

# Wait for a finished status
while not status[0] in ('OK', 'Fejlet'):
    sys.stdout.write("Waiting for scan to finish...\t"
                     + spinner_chars[spinner_counter % len(spinner_chars)]
                     + "\r")
    sys.stdout.flush()
    spinner_counter += 1

    status = wc.get_status(username, password, report_url)
    time.sleep(.5)

print "Scan finished with status %s. Found %d matches." % (status[0],
                                                           status[3])
print "Report available at: %s" % report_url

report = wc.get_report(username, password, report_url)
if args.output_file is not None:
    with open(args.output_file, "w") as f:
        f.write(report.encode('utf-8'))
    print "Saved report as CSV to file:", args.output_file
else:
    print report
