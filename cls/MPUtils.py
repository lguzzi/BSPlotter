import  multiprocessing as mp
from    multiprocessing import managers
import  time, os, sys

class MPManager:
  """Run mapped jobs in worker processes and track their aggregate progress."""
  def __init__(self, threads=1):
    """Initialize a shared progress counter.

    ``threads`` is retained for compatibility; the worker count is provided
    to :meth:`run_parallel`.
    """
    self.progress = mp.Value('f', 0.0)

  def run_parallel(self, function, iterables, threads, debug=False):
    """Map ``function`` over ``iterables`` and return results in input order.

    Args:
      function: Callable invoked once per item.
      iterables: Items passed to ``function``.
      threads: Number of worker processes when ``debug`` is false.
      debug: If true, run calls serially without creating a process pool.
    """
    if not debug:
      with mp.Pool(threads) as pool:
        print('[INFO] running parallel on {} jobs'.format(threads))
        progressbar = mp.Process(target=self._progressbar)
        results = pool.map(function, iterables)
        progressbar.start()
        self.progress.value = 100
        time.sleep(0.1)
        progressbar.terminate()
      print()
    else:
      print('[WARNING] running test job in debug mode')
      results = [function(i) for i in iterables]
    return results

  def _progressbar(self):
    """Print the shared job progress counter until it reaches 100 percent."""
    bar = lambda dim=50: '[{}{}%{}]'.format(
      '#'*int(self.progress.value*dim//100) , 
      int(self.progress.value)               , 
      '-'*int(dim-self.progress.value*dim//100+int(self.progress.value<100)+int(self.progress.value<10))
    )
    while(True):
      dim=min(50, os.get_terminal_size()[0]-10)
      sys.stdout.write('\r%s' %bar(dim))
      sys.stdout.flush()
      time.sleep(.1)
      if self.progress.value==100:
        break
    sys.stdout.write('\r%s\n' %bar(dim))
    sys.stdout.flush()
