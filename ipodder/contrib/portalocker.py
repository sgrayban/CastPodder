# portalocker.py - Cross-platform (posix/nt) API for flock-style file locking.
#                  Requires python 1.5.2 or better.

"""Cross-platform (posix/nt) API for flock-style file locking.

Synopsis:

   import portalocker
   file = open("somefile", "r+")
   portalocker.lock(file, portalocker.LOCK_EX)
   file.seek(12)
   file.write("foo")
   file.close()

If you know what you're doing, you may choose to

   portalocker.unlock(file)

before closing the file, but why?

Methods:

   lock( file, flags )
   unlock( file )

Constants:

   LOCK_EX
   LOCK_SH
   LOCK_NB

I learned the win32 technique for locking files from sample code
provided by John Nielsen <nielsenjf@my-deja.com> in the documentation
that accompanies the win32 modules.

Author: Jonathan Feinberg <jdf@pobox.com>

Modified for CastPodder linux since we dont care or need win32 stuff (grayban)

Version: $Id: portalocker.py 68 2006-04-26 20:14:35Z sgrayban $
"""

import fcntl
LOCK_EX = fcntl.LOCK_EX
LOCK_SH = fcntl.LOCK_SH
LOCK_NB = fcntl.LOCK_NB

def lock(file, flags):
    fcntl.flock(file.fileno(), flags)

def unlock(file):
    fcntl.flock(file.fileno(), fcntl.LOCK_UN)

if __name__ == '__main__':
    from time import time, strftime, localtime
    import sys
    import portalocker

    log = open('log.txt', "a+")
    portalocker.lock(log, portalocker.LOCK_EX|portalocker.LOCK_NB)

    timestamp = strftime("%m/%d/%Y %H:%M:%S\n", localtime(time()))
    log.write( timestamp )

    print "Wrote lines. Hit enter to release lock."
    dummy = sys.stdin.readline()

    log.close()
