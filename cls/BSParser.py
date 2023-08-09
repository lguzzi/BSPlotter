import os, sys
sys.path.append('cls')
from MPUtils  import MPManager
from OMSUtils import fetch_data, get_cookie
from datetime import datetime

class BSParser:
  '''class to handle beamspot file operations
  '''
  CANFAIL=False
  COOKIE = get_cookie('https://cmsoms.cern.ch/')
  MANAGER=MPManager()

  def __init__(self, file):
    self.filename = os.path.basename(file)
    self.beamspot = BSParser.readTxtFile(file, canfail=BSParser.CANFAIL)
  
  def fetch_from_OMS(self):
    ''' fetch data from OMS with parallel streams
    '''
    print("[INFO] fetching data from OMS for", self.filename)    
    fetched = BSParser.MANAGER.run_parallel(
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
    beamspot[(run,ls,le)]['fillstamp'] = toepoch(filljsn['data']['attributes']['start_time'])
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
  def readTxtFile(file, canfail=False):
    '''read a .txt beamspot file written in the 
    beamspot producer format and save the results
    in a dictionary 
    {
      (run,ls_start,ls_end): info
    }
    Use canfail to select also non-converging fits
    '''
    with open(file, 'r') as ifile:
      beamspot = {
        ( int(lines[0]              ), 
          int(lines[3].split(' ')[1]), 
          int(lines[3].split(' ')[3])): {
          'beginTime' : int   (lines[1] .split(' ')[-1]),
          'endTime'   : int   (lines[2] .split(' ')[-1]),
          'fittype'   : int   (lines[4] .split(' ')[-1]),
          'x'         : float (lines[5] .split(' ')[-1]),
          'y'         : float (lines[6] .split(' ')[-1]),
          'z'         : float (lines[7] .split(' ')[-1]),
          'widthZ'    : float (lines[8] .split(' ')[-1]),
          'dxdz'      : float (lines[9] .split(' ')[-1]),
          'dydz'      : float (lines[10].split(' ')[-1]),
          'widthX'    : float (lines[11].split(' ')[-1]),
          'widthY'    : float (lines[12].split(' ')[-1]),
          'emittanceX': float (lines[20].split(' ')[-1]),
          'emittanceY': float (lines[21].split(' ')[-1]),
          'betaStar'  : float (lines[22].split(' ')[-1]),
          'covariance': [[float(e) for e in row.split(' ')[1:] if len(e)] for row in lines[13:20]],
        } for lines in [d.split('\n') for d in ifile.read().split('Runnumber ') if len(d)]
        if int(lines[4] .split(' ')[-1])==2 or canfail
      }
    return beamspot