import  multiprocessing as mp
from    multiprocessing import managers
import  time, os, sys

class MPManager:
  ''' manage multiprocess operations
  '''
  def __init__(self, threads=1):
    self.progress = mp.Value('f', 0.0)

  def run_parallel(self, function, iterables, threads, debug=False):
    ''' run a function in parallel and print a progressbar
    '''
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
    ''' base function to print a progressbar
    '''
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
