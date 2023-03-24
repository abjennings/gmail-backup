# -*- coding: utf-8 -*-
import imaplib
import os
import getpass
import re


UID_RE = re.compile(r"\d+\s+\(UID (\d+)\)$")
FILE_RE = re.compile(r"(\d+).eml$")


def set_email_server():

    print("Hi, Select from the list of Available Email clients below: ")
    while True:
        try:
            email_choice = int(raw_input("1. Gmail\n2. Amazon Work Mail\nEnter Choice: "))
        except ValueError:
            print"That is an invalid input, try again"
            continue
        if email_choice == 1:
            email_server = 'imap.gmail.com'
            options = ['INBOX', '[Gmail]/All Mail', '[Gmail]/DRAFTS', '[Gmail]/Sent Email']
            break
        elif email_choice == 2:

            print('Please enter the IMAP server Address of your amazon imap server')
            email_server = raw_input("leave blank for default ('imap.mail.us-west-2.awsapps.com'): ")
            email_server = 'imap.mail.us-west-2.awsapps.com' if email_server == '' else email_server
            options = ['INBOX', 'Sent Items', 'Drafts']
            break
        else:
            print('That is an invalid response, please try again')
            continue

    return email_server, options


def getUIDForMessage(svr, n):
    resp, lst = svr.fetch(n, 'UID')
    m = UID_RE.match(lst[0])
    if not m:
        raise Exception(
            "Internal error parsing UID response: %s %s.  Please try again" % (resp, lst))
    return m.group(1)


def download_message(svr, n, dirpath, basename):
    resp, lst = svr.fetch(n, '(RFC822)')
    if resp != 'OK':
        raise Exception("Bad response: %s %s" % (resp, lst))
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    fpath = os.path.join(dirpath, basename)
    f = open(fpath, 'w+')
    f.write(lst[0][1])
    f.close()


def UIDFromFilename(fname):
    m = FILE_RE.match(fname)
    if m:
        return int(m.group(1))


def get_credentials():
    user = raw_input("Email address: ")
    pwd = getpass.getpass("Email password: ")
    return user, pwd


def get_folder_to_backup(options):
    max_opt = len(options)
    while True:
        try:

            print("select folder you want to backup...")
            for i in range(1, max_opt + 1):
                print('{} -> {}'.format(i, options[i - 1]))

            choice = int(raw_input("choice: "))
        except ValueError:
            print"That is an invalid input, try again"
            continue
        if choice not in range(1, max_opt + 1):
            print('That is an invalid response, please try again')
            continue
        else:
            folder_name = options[choice - 1]  # selecting folder from options list
            break

    return folder_name


def do_backup():

    email_server, options = set_email_server()
    svr = imaplib.IMAP4_SSL(email_server, 993)  # default imap port 993
    user, pwd = get_credentials()
    resp = svr.login(user, pwd)
    resp = resp[0]
    if resp == 'OK':
        print('Login successful')
    else:
        print('There is a fatal error somewhere')

    email_folder_name = get_folder_to_backup(options)

    resp, countstr = svr.select(email_folder_name, True)
    count = int(countstr[0])

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
        basename = uid+'.eml'

        dir_path = os.path.join('backup', user, email_folder_name)
        print "Downloading %d/%d (UID: %s)" % (i, count, basename)
        download_message(svr, i, dir_path, basename)

    svr.close()
    svr.logout()


if __name__ == "__main__":
    do_backup()
