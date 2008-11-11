"""
The Make module.  This module provides an interface to `make'.
"""
from __future__ import absolute_import

from os import getenv

__all__ = ['clean_log', 'env', 'make_target', 'no_opt', 'pre_cmd', 'SUCCESS']

env = {}  #: The environment flags to pass to make, aka -D...
no_opt = False  #: Indicate if we should not issue a command
pre_cmd = []  #: Prepend to command
SUCCESS = 0  #: The value returns by a program on success
am_root = getenv('USER')  #: Indicate if we are root
password = None  #: Password to access root status (via su or sudo)

env["PORTSDIR"] = getenv("PORTSDIR", "/usr/ports/")  #: Location of ports
env["BATCH"] = None  #: Default to use batch mode
env["NOCLEANDEPENDS"] = None  #: Default to only clean ports

def check_password(passwd):
  """
     Check the password to gain root status.  If the password is correct then
     it is stored locally.

     @param passwd: The password to use.
     @type passwd: C{str}
     @return: If the password gets us user privilage
     @rtype: C{bool}
  """
  from subprocess import Popen, PIPE, STDOUT

  global am_root, password

  if am_root == 'root' or password is not None:
    return True

  try:
    sudo = ['sudo', '-S', '--']
    cmd = Popen(sudo + ['cat'], stdin=PIPE, stdout=PIPE, stderr=STDOUT,
                                         close_fds=True)
    cmd.stdin.write(passwd)
    cmd.stdin.close()
    if cmd.wait() is SUCCESS:
      am_root = sudo
      password = passwd
      return True
  except OSError:
    # SUDO does not exist, try su
    return False

def log_files(origin):
  """
     Creates the log file handler for the given port.  This is for both stdout
     and stderr.

     @param origin: The ports origin
     @type origin: C{str}
     @return: The stdout and stderr file handlers
     @rtype: C{(file, file)}
  """
  from os.path import join

  from pypkg.env import dirs

  log = open(join(dirs['log_port'], origin.replace('/', '_')), 'a')
  return log, log

def cmdtostr(args):
  """
     Convert a list of arguments to a single string.

     @param args: The list of arguments
     @type args: C{[str]}
     @return: The arguments as a string
     @rtype: C{str}
  """
  argstr = []
  for i in args:
    argstr.append(i.replace("\\", "\\\\").replace('"', '\\"').\
                    replace("'", "\\'").replace('\n', '\\\n'))
    if ' ' in i or '\t' in i or '\n' in i:
      argstr[-1] = '"%s"' & argstr[-1]
  return ' '.join(argstr)

def get_pipe(pipe, origin):
  """
     Returns the appropriate pipes.  None is the default (pipe to logfile),
     False is not piping, True is pipe stdout and stderr and file object is
     pipe to the file (both stdout and stderr)/

     @param pipe: The type of pipe requested.
     @type pipe: C{bool|None|file}
     @param origin: The for for which to run create logfiles for
     @type origin: C{str}
     @return: Tuple of pipes (stdin, stdout, stderr)
     @rtype: C{(None|PIPE|file}
  """
  from subprocess import PIPE, STDOUT

  if pipe is True:
    return PIPE, PIPE, STDOUT
  elif pipe:
    return PIPE, pipe, STDOUT
  elif pipe is False:
    return None, None, None
  else:
    stdout, stderr = log_files(origin)
    return PIPE, stdout, stderr


def make_target(origin, args, pipe=None, priv=False):
  """
     Run make to build a target with the given arguments and the appropriate
     addition settings

     @param origin: The port for which to run make
     @type origin: C{str}
     @param args: Targets and arguments for make
     @type args: C{(str)}
     @param pipe: Indicate if the make argument output must be piped
     @type pipe: C{bool|file}
     @param priv: Indicate if the make command needs to be privilaged
     @type priv: C{bool}
     @return: The make process interface
     @rtype: C{Popen}
  """
  from os.path import join
  from subprocess import Popen

  if isinstance(args, str):
    args = [args]
  args = args + [v and '%s="%s"' % (k, v) or "-D%s" % k for k, v in env.items()
                  if (k, v) != ("PORTSDIR", "/usr/ports/") and
                    (args[0], k) != ('config', "BATCH") and
                    (k != "NOCLEANDEPENDS" or 'clean' in args)]

  stdin, stdout, stderr = get_pipe(pipe, origin)

  if pipe is False and not no_opt:
    from pypkg.monitor import monitor
    monitor.pause()

  try:
    args = pre_cmd + ['make', '-C', join(env["PORTSDIR"], origin)] + args
    if pipe or not no_opt:
      if priv and isinstance(am_root, (list, tuple)):
        args = am_root + args
      make = Popen(args, stdin=stdin, stdout=stdout, stderr=stderr,
                  close_fds=True)
      if stdin:
        if priv and isinstance(am_root, (list, tuple)):
          make.stdin.write(password)
        make.stdin.close()
      elif pipe is False:
        make.wait()
    else:
      print cmdtostr(args)
      make = PopenNone()
  finally:
    if pipe is False and not no_opt:
      monitor.resume()

  return make


class PopenNone(object):
  """
     An empty replacement for Popen
  """

  returncode = SUCCESS
  pid = -1

  stdin  = None
  stdout = None
  stderr = None

  @staticmethod
  def wait():
    """
       Return SUCCESS

       @return: Success
       @rtype: C{int}
    """
    return PopenNone.returncode

  @staticmethod
  def poll():
    """
       Return SUCCESS

       @return: Success
       @rtype: C{int}
    """
    return PopenNone.returncode

  @staticmethod
  def communicate(input=None):
    """
       Communicate with the process

       @param input: Input to the port
       @type input: C{str}
       @return: The processes output
       @rtype: C{(None, None)}
    """
    return (PopenNone.stdout, PopenNone.stderr)
