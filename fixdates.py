# -*- coding: utf-8 -*-

import re
import os
import email
import email.utils
import datetime
import time
import calendar


FILE_RE = re.compile(r"(\d+).eml$")
LAST_DATE_FIXED_FILENAME = "last_email_fixed.dat"

def get_message_ctime(d):
    orig_d = d
    dt_src = email.utils.parsedate_tz(d)
    if not dt_src:
        return None
    if not dt_src[-1]:
        # TZ INFO IS MESSY
        if " --" in d:
            d = d.replace(" --", " -")
            dt_src = email.utils.parsedate_tz(d)
    try:
        dt = datetime.datetime(*dt_src[:6])
    except Exception, e:
        print e
        print "orig date: %r, curr date: %r, dt_src: %r" % (orig_d, d, dt_src)
        return None
    if dt_src[-1]:
        dt = dt-datetime.timedelta(seconds=dt_src[-1])
    dt = datetime.datetime.fromtimestamp(calendar.timegm(dt.timetuple()))
    message_ctime = time.mktime(dt.timetuple())
    return message_ctime


try:
    with open(LAST_DATE_FIXED_FILENAME) as f:
        last_file_int_fixed = int(f.read().strip())
except:
    last_file_int_fixed = -1


EMAIL_NUMBERS = []
for fname in os.listdir("."):
    m = FILE_RE.match(fname)
    if m:
        file_int = int(m.group(1))
        if file_int > last_file_int_fixed:
            EMAIL_NUMBERS.append(int(m.group(1)))


EMAIL_NUMBERS.sort()
for i,file_int in enumerate(EMAIL_NUMBERS):
    fname = str(file_int)+".eml"
    print "(%d of %d) %s" % (i+1, len(EMAIL_NUMBERS), fname)

    with open(fname) as f:
        file_contents = f.read()
    message = email.message_from_string(file_contents)
    message_ctime = get_message_ctime(message['date'])
    if message_ctime:
        os.utime(fname, (message_ctime, message_ctime))

if EMAIL_NUMBERS:
    f = open(LAST_DATE_FIXED_FILENAME, 'w')
    f.write(str(EMAIL_NUMBERS[-1]))
    f.close()
