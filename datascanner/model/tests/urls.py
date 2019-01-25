from ..smb import SMBHandle, SMBSource
from ..core import Source
from ..file import FilesystemSource

from pathlib import Path

sources_and_urls = [
    (FilesystemSource("/usr"),
        "file:///usr"),

    (SMBSource("//10.0.0.30/Share$/Documents"),
        "smb://10.0.0.30/Share%24/Documents"),
    (SMBSource("//10.0.0.30/Share$/Documents", "FaithfullA"),
        "smb://FaithfullA@10.0.0.30/Share%24/Documents"),
    (SMBSource("//10.0.0.30/Share$/Documents", "FaithfullA", "secretpassword"),
        "smb://FaithfullA:secretpassword@10.0.0.30/Share%24/Documents"),
    (SMBSource("//10.0.0.30/Share$/Documents", "FaithfullA", "secretpassword", "SYSGRP"),
        "smb://SYSGRP;FaithfullA:secretpassword@10.0.0.30/Share%24/Documents"),
    (SMBSource("//10.0.0.30/Share$/Documents", "FaithfullA", None, "SYSGRP"),
        "smb://SYSGRP;FaithfullA@10.0.0.30/Share%24/Documents"),
]

def equality_check(generated, reference):
    try:
        print("{0} == {1}?".format(generated, reference))
        assert generated == reference
        print("\tOK")
        return True
    except AssertionError as e:
        print("\tFAIL")
        return False

if __name__ == '__main__':
    success, failure = 0, 0
    for source, url in sources_and_urls:
        generated_url = source.to_url()
        if equality_check(generated_url, url):
            success += 1
        else:
            failure += 1
        generated_source = Source.from_url(generated_url)
        if equality_check(generated_source, source):
            success += 1
        else:
            failure += 1
    print("Ran {0} tests, {1} successes, {2} failures".format(
            success + failure, success, failure))
