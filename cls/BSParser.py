import os, sys
sys.path.append('cls')
from MPUtils  import MPManager
from OMSUtils import fetch_data, get_cookie
from datetime import datetime
from BSFormat import BSFormatVanilla, BSFormatVdM

class BSParser:
  '''class to handle beamspot file operations
  '''
  CANFAIL=False
  COOKIE = get_cookie('https://cmsoms.cern.ch/')
  MANAGER=MPManager()

  def __init__(self, file, threads=1, flavour='default'):
    self.filename = os.path.basename(file)
    self.beamspot = BSParser.readTxtFile(file, canfail=BSParser.CANFAIL, flavour=flavour)
    self.threads  = threads
    self.flavour  = flavour
  
  def fetch_from_OMS(self):
    ''' fetch data from OMS with parallel streams
    '''
    print("[INFO] fetching data from OMS for", self.filename)    
    fetched = BSParser.MANAGER.run_parallel(threads=self.threads,
      function=BSParser._fetch, 
      iterables=[(r,ls,le,len(self.beamspot.keys())) for (r,ls,le) in self.beamspot.keys()]
    )
    fetched = {k:v for f in fetched for k,v in f.items()}
    for k in fetched.keys():
      self.beamspot[k] = {**self.beamspot[k],**fetched[k]}
  
  @staticmethod
  def _fetch(entry):
    ''' base function for fetching BS information from OMS
    '''
    run,ls,le,tot = entry
    URL     = "https://cmsoms.cern.ch/agg/api/v1/{K}/{ID}/"
    toepoch = lambda tme: (datetime.strptime(tme, "%Y-%m-%dT%H:%M:%SZ")-datetime(1970,1,1)).total_seconds()
    runjsn  = fetch_data(cookie=BSParser.COOKIE, url=URL.format(K='runs'         , ID=run))
    lsjsn   = fetch_data(cookie=BSParser.COOKIE, url=URL.format(K='lumisections' , ID='_'.join([str(run), str(ls)])))
    lejsn   = fetch_data(cookie=BSParser.COOKIE, url=URL.format(K='lumisections' , ID='_'.join([str(run), str(le)]))) if le!=ls else lsjsn
    filljsn = fetch_data(cookie=BSParser.COOKIE, url=URL.format(K='fills'        , ID=runjsn['data']['attributes']['fill_number']))
    beamspot = {}
    beamspot[(run,ls,le)] = {}
    beamspot[(run,ls,le)]['fill'     ] = filljsn['data']['id']
    beamspot[(run,ls,le)]['run'      ] = runjsn ['data']['id']
    beamspot[(run,ls,le)]['fillstamp'] = toepoch(filljsn['data']['attributes']['start_time'])
    beamspot[(run,ls,le)]['runstamp' ] = toepoch(runjsn ['data']['attributes']['start_time'])
    beamspot[(run,ls,le)]['date'     ] = lsjsn['data']['attributes']['start_time'] 
    beamspot[(run,ls,le)]['timestamp'] = 0.5*(
      toepoch(lejsn['data']['attributes']['end_time'  ]) +
      toepoch(lsjsn['data']['attributes']['start_time'])
    )
    beamspot[(run,ls,le)]['timewidth'] = (
      toepoch(lejsn['data']['attributes']['end_time'  ]) -
      toepoch(lsjsn['data']['attributes']['start_time'])
    )
    BSParser.MANAGER.progress.value += 100./tot
    return beamspot

  @staticmethod
  def readTxtFile(file, canfail=False, flavour='default'):
    '''read a .txt beamspot file written in the 
    beamspot producer format and save the results
    in a dictionary 
    {
      (run,ls_start,ls_end): info
    }
    Use --canfail to select also non-converging fits
    '''
    with open(file, 'r') as ifile:
      beamspot = BSFormatVdM(ifile, canfail).get() if flavour=='vdm' else BSFormatVanilla(ifile, canfail).get()
    
    return beamspot