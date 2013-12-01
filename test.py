import sys
import dobackup

if sys.argv[1:]:
    creds_file = sys.argv[1]
else:
    creds_file = None
_saved_get_creds = dobackup.get_credentials
    

def test_get_credentials():
    if creds_file:
        print "Reading test creds from %s" % creds_file
        with open(creds_file) as f:
            pieces = f.read().split("\n")
            user = pieces[0]
            pwd = pieces[1]
            if pieces[2:]:
                print "Using folder %r" % pieces[2]
                dobackup.GMAIL_FOLDER_NAME = pieces[2]
    else:
        user, pwd = _saved_get_creds()
    return user, pwd

# Monkey-patch dobackup for automated testing
dobackup.get_credentials = test_get_credentials

dobackup.do_backup()
