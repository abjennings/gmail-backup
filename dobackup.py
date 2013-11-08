import imaplib, os, getpass, re, email, email.utils, datetime, time, calendar

uidre = re.compile(r"\d+\s+\(UID (\d+)\)$")
def getUIDForMessage(n):
	resp, lst = svr.fetch(n, 'UID')
	m = uidre.match(lst[0])
	if not m:
		raise Exception("Internal error parsing UID response: %s %s.  Please try again" % (resp, lst))
	return m.group(1)
	

def downloadMessage(n, fname):
	resp, lst = svr.fetch(n, '(RFC822)')
	if resp!='OK':
		raise Exception("Bad response: %s %s" % (resp, lst))
	f = open(fname, 'w')
	f.write(lst[0][1])
	f.close()
	message = email.message_from_string(lst[0][1])
	dt_src = email.utils.parsedate_tz(message['date'])
	if dt_src:
		utc_dt = datetime.datetime(*dt_src[:6])-datetime.timedelta(seconds= dt_src[-1])
		dt = datetime.datetime.fromtimestamp(calendar.timegm(utc_dt.timetuple()))
		message_ctime = time.mktime(dt.timetuple())
		os.utime(fname, (message_ctime, message_ctime))


filere = re.compile(r"(\d+).eml$")
def UIDFromFilename(fname):
	m = filere.match(fname)
	if m:
		return int(m.group(1))


svr = imaplib.IMAP4_SSL('imap.gmail.com')
svr.login(raw_input("Gmail address: "), getpass.getpass("Gmail password: "))

resp, [countstr] = svr.select("[Gmail]/All Mail", True)
count = int(countstr)

existing_files = os.listdir(".")
if existing_files:
    lastdownloaded = max(UIDFromFilename(f) for f in existing_files)
else:
    lastdownloaded = 0


# A simple binary search to see where we left off
gotten, ungotten = 0, count+1
while ungotten-gotten>1:
	attempt = (gotten+ungotten)/2
	uid = getUIDForMessage(attempt)
	if int(uid)<=lastdownloaded:
		print "Finding starting point: %d/%d (UID: %s) too low" % (attempt, count, uid)
		gotten = attempt
	else:
		print "Finding starting point: %d/%d (UID: %s) too high" % (attempt, count, uid)
		ungotten = attempt


# The download loop
for i in range(ungotten, count+1):
	uid = getUIDForMessage(i)
	print "Downloading %d/%d (UID: %s)" % (i, count, uid)
	downloadMessage(i, uid+'.eml')


svr.close()
svr.logout()
