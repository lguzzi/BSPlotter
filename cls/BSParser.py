import os, sys
sys.path.append('cls')
from MPUtils  import MPManagerThreads
from OMSUtils import fetch_data, get_authenticator
from datetime import datetime
from BSFormat import FormatInputTxt, FormatOutputTxt
import uncertainties as unc
import numpy as np

class BSParser:
  '''class to handle beamspot file operations
  '''
  DEBUG=False
  STREAMS=5
  AUTHENTICATOR=get_authenticator(verbose=DEBUG)

  def __init__(self, file, flavour='default', streams=1, fittype=2):
    self.filename = os.path.basename(file)
    self.beamspot = BSParser.readTxtFile(file, fittype=fittype, flavour=flavour)
    self.flavour  = flavour
    self.STREAMS  = streams

  def writeTxtFile(self, filename):
    ''' write a .txt file with specific formatting
    '''
    formatter = FormatOutputTxt(self.beamspot, formatting=self.flavour)

  def fetch_timestamps_from_OMS(self):
    ''' fetch timestamps from OMS with parallel streams
    '''
    print("[INFO] fetching data from OMS for", self.filename)
    entries = [(r,ls,le,len(self.beamspot.keys())) for (r,ls,le) in self.beamspot.keys()]
    fetched = MPManagerThreads(workers=self.STREAMS)(BSParser._fetch_timestamps_from_OMS)(*entries)
    fetched = {k:v for f in fetched for k,v in f.items()}
    for k in fetched.keys():
      self.beamspot[k] = {**self.beamspot[k],**fetched[k]}
      BSParser._compute_proper_widths(self.beamspot[k])

  @staticmethod
  def _fetch_timestamps_from_OMS(run, lumistart, lumiend, size):
    ''' base function for fetching BS information from OMS
    '''
    toepoch = lambda tme: (datetime.strptime(tme, "%Y-%m-%dT%H:%M:%SZ")-datetime(1970,1,1)).total_seconds()
    runjsn  = fetch_data(datatype='runs'         , dataid=run, omsapi=BSParser.AUTHENTICATOR)
    lsjsn   = fetch_data(datatype='lumisections' , dataid='_'.join([str(run), str(lumistart)]), omsapi=BSParser.AUTHENTICATOR)
    lejsn   = fetch_data(datatype='lumisections' , dataid='_'.join([str(run), str(lumiend  )]), omsapi=BSParser.AUTHENTICATOR) if lumiend!=lumistart else lsjsn
    filljsn = fetch_data(datatype='fills'        , dataid=runjsn['data']['attributes']['fill_number'], omsapi=BSParser.AUTHENTICATOR)
    lumlist = [lsjsn]+[
      fetch_data(datatype='lumisections', dataid='_'.join([str(run), str(l)]), omsapi=BSParser.AUTHENTICATOR) for l in range(lumistart+1,lumiend)
    ]+[lejsn] if lumiend!=lumistart else [lsjsn]

    beamspot = {}
    beamspot[(run,lumistart,lumiend)] = {}
    beamspot[(run,lumistart,lumiend)]['fill'      ] = filljsn['data']['id']
    beamspot[(run,lumistart,lumiend)]['run'       ] = runjsn ['data']['id']
    beamspot[(run,lumistart,lumiend)]['fillstamp' ] = toepoch(filljsn['data']['attributes']['start_time'])
    beamspot[(run,lumistart,lumiend)]['runstamp'  ] = toepoch(runjsn ['data']['attributes']['start_time'])
    beamspot[(run,lumistart,lumiend)]['date'      ] = lsjsn['data']['attributes']['start_time'] 
    beamspot[(run,lumistart,lumiend)]['IOVbegin'  ] = toepoch(lsjsn['data']['attributes']['start_time'])
    beamspot[(run,lumistart,lumiend)]['IOVend'    ] = toepoch(lsjsn['data']['attributes']['end_time'  ])
    beamspot[(run,lumistart,lumiend)]['init_lumi' ] = sum(lum['data']['attributes']['init_lumi'] for lum in lumlist)  # 10^31 /s/cm^2
    beamspot[(run,lumistart,lumiend)]['avg_pu'    ] = sum(lum['data']['attributes']['pileup']    for lum in lumlist)/len(lumlist)
    beamspot[(run,lumistart,lumiend)]['timestamp' ] = 0.5*(
      toepoch(lejsn['data']['attributes']['end_time'  ]) +
      toepoch(lsjsn['data']['attributes']['start_time'])
    )
    beamspot[(run,lumistart,lumiend)]['timewidth'] = (
      toepoch(lejsn['data']['attributes']['end_time'  ]) -
      toepoch(lsjsn['data']['attributes']['start_time'])
    )
    #BSParser.MANAGER.progress.value += 100./tot
    return beamspot

  @staticmethod
  def _compute_proper_widths(beamspot):
    ''' Rotate back the covariance matrix by -dx/dz and -dy/dz.
    The sigma_x and sigma_y *of the luminous region itself* are set.
    The dx/dy rotation is not corrected (but it's small).
    The effect on sigma_z is neglected as it's small.
    '''
    # https://github.com/MilanoBicocca-pix/cmssw/blob/2d1e039a413496536abe6931561ea826025dc728/RecoVertex/BeamSpotProducer/src/PVFitter.cc#L302-L312
    # https://github.com/MilanoBicocca-pix/cmssw/blob/2d1e039a413496536abe6931561ea826025dc728/RecoVertex/BeamSpotProducer/src/PVFitter.cc#L241-L252
    widthXerr = beamspot['covariance'][6][6]
    widthYerr = beamspot['covariance'][7][7]
    widthZerr = beamspot['covariance'][3][3]
    dxdzerr   = beamspot['covariance'][4][4]
    dydzerr   = beamspot['covariance'][5][5]
    XYerr     = beamspot['covariance'][0][1]

    alpha = unc.ufloat(-beamspot['dydz'], dydzerr)
    beta  = unc.ufloat(-beamspot['dxdz'], dxdzerr)

    s_xx = unc.ufloat(np.power(beamspot['widthX'], 2), np.power(widthXerr, 2))
    s_yy = unc.ufloat(np.power(beamspot['widthY'], 2), np.power(widthYerr, 2))
    s_zz = unc.ufloat(np.power(beamspot['widthZ'], 2), np.power(widthZerr, 2))

    s_xz  = beta *(s_zz-s_xx)+alpha*unc.ufloat(XYerr, abs(XYerr)) # 100% uncertainty on XY correlation, as we don't save it...
    s_yz  = alpha*(s_yy-s_zz)-beta *unc.ufloat(XYerr, abs(XYerr)) # 100% uncertainty on XY correlation, as we don't save it...

    s_xx_true = s_xx-2.*beta *s_xz+np.power(beta , 2)*s_zz
    s_yy_true = s_yy+2.*alpha*s_yz+np.power(alpha, 2)*s_zz
    s_zz_true = s_zz

    beamspot['widthXTrue'] = np.sqrt(max(0., s_xx_true.n))
    beamspot['widthYTrue'] = np.sqrt(max(0., s_yy_true.n))
    beamspot['widthZTrue'] = np.sqrt(max(0., s_zz_true.n))

    beamspot['widthXTrueerr'] = np.sqrt(max(0., s_xx_true.s))
    beamspot['widthYTrueerr'] = np.sqrt(max(0., s_yy_true.s))
    beamspot['widthZTrueerr'] = np.sqrt(max(0., s_zz_true.s))

  @staticmethod
  def readTxtFile(file, fittype=2, flavour='default'):
    '''read a .txt beamspot file written in the 
    beamspot producer format and save the results
    in a dictionary 
    {
      (run,ls_start,ls_end): info
    }
    '''
    with open(file, 'r') as ifile:
      beamspot = FormatInputTxt(ifile, fittype)
    
    return beamspot
