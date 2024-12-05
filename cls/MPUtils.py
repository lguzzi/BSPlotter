import concurrent.futures
import functools
import time

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

def MPManagerThreads(workers=1):
  ''' thread parallelization should only be used on tasks which do not load the CPU 
    (eg. http requests) due to the python GIL. However, tsgauth is not thread safe.
  '''
  print('workers', workers)
  def outer(func):
    def inner(*args, **kwargs):
      progress = mp.Value('f', 0.0)
      print('[INFO] running parallel on {} jobs'.format(workers))
      progressbar = mp.Process(target=_progressbar)
      progressbar.start()
      with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        results = []
        for arg_set in args:
          results.append(executor.submit(func, *arg_set, **kwargs) for arg_set in args)
          progress += 1./len(args)
          

      return [result.result() for result in results]
    return inner
  return outer

if __name__=='__main__':
  '''testing purpose
  '''
  import argparse
  parser = argparse.ArgumentParser('''Test environment of MPUtils''')
  parser.add_argument('--threads', default=1, type=int, help='number of threads or processes to use for the test')
  args = parser.parse_args()
  
  @MPManagerThreads(workers=args.threads)
  def threadtest(x, y):
    print ('x + y =', x+y)
    time.sleep(5)
  results = threadtest((1,2), (3,4), (5,6))