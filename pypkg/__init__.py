"""
The pypkg module.
"""
from __future__ import absolute_import

def run_main(main):
  """
     Run the main function in its own thread and then runs the exit handler
     function.  This function does not return.

     @param main: The main function to execute
     @type main: C{callable}
  """
  from threading import Thread

  from pypkg.exit import exit_handler, terminate

  assert callable(main)

  def call():
    """
       Call the main function and then start the idle checker.
    """
    try:
      main()
    except SystemExit:
      pass
    except BaseException:
      from logging import getLogger
      getLogger("pypkg").exception("Main function failed")
    terminate()

  Thread(target=call).start()
  exit_handler.run()
