# -*- coding: utf-8 -*-
import imaplib
import os
import getpass
import re


UID_RE = re.compile(r"\d+\s+\(UID (\d+)\)$")
FILE_RE = re.compile(r"(\d+).eml$")
GMAIL_FOLDER_NAME = "[Gmail]/All Mail"


def getUIDForMessage(svr, n):
    resp, lst = svr.fetch(n, 'UID')
    m = UID_RE.match(lst[0])
    if not m:
        raise Exception(
            "Internal error parsing UID response: %s %s.  Please try again" % (resp, lst))
    return m.group(1)


def downloadMessage(svr, n, fname):
    resp, lst = svr.fetch(n, '(RFC822)')
    if resp != 'OK':
        raise Exception("Bad response: %s %s" % (resp, lst))
    f = open(fname, 'w')
    f.write(lst[0][1])
    f.close()


def UIDFromFilename(fname):
    m = FILE_RE.match(fname)
    if m:
        return int(m.group(1))


def get_credentials():
    user = os.environ.get("DOBACKUP_GMAIL_APP_USER", None) or raw_input("Gmail address: ")
    pwd = os.environ.get("DOBACKUP_GMAIL_APP_PWD", None) or getpass.getpass("Gmail password: ")
    return user, pwd

def gmail_folder():
    return os.environ.get("DOBACKUP_GMAIL_LABEL", GMAIL_FOLDER_NAME) 

def save_folder_path():
    folder = os.environ.get("DOBACKUP_SAVE_FOLDER", "") # i.e. "./"
    os.makedirs(folder, exist_ok=True)
    return folder

def do_backup():
    svr = imaplib.IMAP4_SSL('imap.gmail.com')
    user, pwd = get_credentials()
    svr.login(user, pwd)

    resp, [countstr] = svr.select(gmail_folder(), True)
    count = int(countstr)

    existing_files = os.listdir(".")
    lastdownloaded = max(UIDFromFilename(f)
                         for f in existing_files) if existing_files else 0

    # A simple binary search to see where we left off
    gotten, ungotten = 0, count + 1
    while (ungotten - gotten) > 1:
        attempt = (gotten + ungotten) / 2
        uid = getUIDForMessage(svr, attempt)
        if int(uid) <= lastdownloaded:
            print "Finding starting point: %d/%d (UID: %s) too low" % (attempt, count, uid)
            gotten = attempt
        else:
            print "Finding starting point: %d/%d (UID: %s) too high" % (attempt, count, uid)
            ungotten = attempt

    # The download loop
    for i in range(ungotten, count + 1):
        uid = getUIDForMessage(svr, i)
        print "Downloading %d/%d (UID: %s)" % (i, count, uid)
        filepath = save_folder_path() + uid + '.eml'
        downloadMessage(svr, i, filepath)

    svr.close()
    svr.logout()

if __name__ == "__main__":
    do_backup()
