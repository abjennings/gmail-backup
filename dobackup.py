import imaplib, os, getpass, re, email, email.utils, datetime, time, calendar, sys

uidre = re.compile(r"\d+\s+\(UID (\d+)\)$")
def getUIDForMessage(n):
	resp, lst = svr.fetch(n, 'UID')
	m = uidre.match(lst[0])
	if not m:
		raise Exception("Internal error parsing UID response: %s %s.  Please try again" % (resp, lst))
	return m.group(1)
	

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
		dt = dt-datetime.timedelta(seconds= dt_src[-1])
	dt = datetime.datetime.fromtimestamp(calendar.timegm(dt.timetuple()))
	message_ctime = time.mktime(dt.timetuple())
	return message_ctime
	


def downloadMessage(n, fname):
	resp, lst = svr.fetch(n, '(RFC822)')
	if resp!='OK':
		raise Exception("Bad response: %s %s" % (resp, lst))
	f = open(fname, 'w')
	f.write(lst[0][1])
	f.close()
	message = email.message_from_string(lst[0][1])
	message_ctime = get_message_ctime(message['date'])
	if message_ctime:
		os.utime(fname, (message_ctime, message_ctime))
	

filere = re.compile(r"(\d+).eml$")
def UIDFromFilename(fname):
	m = filere.match(fname)
	if m:
		return int(m.group(1))


svr = imaplib.IMAP4_SSL('imap.gmail.com')

def get_credentials():
	for a in sys.argv[1:]:
		if a.startswith("--creds="):
			# --creds= is a file with TWO lines user\npwd
			with open(a.split("=", 1)[-1]) as f:
				user, pwd = f.read().strip().split("\n", 1)
			return user, pwd
	
	user = raw_input("Gmail address: ")
	pwd = getpass.getpass("Gmail password: ")
	return user, pwd
	
user, pwd = get_credentials()
svr.login(user, pwd)

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
