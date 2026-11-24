import os, sys, math
sys.path.append('cls')
from MPUtils  import parallelize
from OMSUtils import fetch_data, get_authenticator
from datetime import datetime
from BSFormat import FormatInputTxt, FormatOutputTxt
from threading import Lock
import uncertainties as unc
import numpy as np

class BSParser:
  '''class to handle beamspot file operations
  '''
  NTHREADS=1
  DEBUG=False
  AUTHENTICATOR=get_authenticator(verbose=DEBUG)

  def __init__(self, file, flavour='default', fittype=2):
    # trigger the web authentication to avoid multiple authentications in parallel threads
    authenticate = fetch_data(datatype='runs', dataid=333333, omsapi=BSParser.AUTHENTICATOR)
    self.filename = os.path.basename(file)
    self.beamspot = BSParser.readTxtFile(file, fittype=fittype, flavour=flavour)
    self.flavour  = flavour
    # FT auxiliaries
    self.updatelock = Lock()

  def fetch_timestamps_from_OMS(self):
    ''' fetch timestamps from OMS with parallel streams
    '''
    print("[INFO] fetching data from OMS for", self.filename)
    iterables = [(r,ls,le,len(self.beamspot.keys())) for (r,ls,le) in self.beamspot.keys()]
    self._fetch_timestamps_from_OMS(iterables, nthreads=BSParser.NTHREADS, debug=BSParser.DEBUG)
    self._compute_proper_widths(self.beamspot, nthreads=BSParser.NTHREADS, debug=BSParser.DEBUG)

  @parallelize
  def _fetch_timestamps_from_OMS(self, entry):
    ''' base function for fetching BS information from OMS
    '''
    run,ls,le,tot = entry
    toepoch = lambda tme: (datetime.strptime(tme, "%Y-%m-%dT%H:%M:%SZ")-datetime(1970,1,1)).total_seconds()
    runjsn  = fetch_data(datatype='runs'         , dataid=run, omsapi=BSParser.AUTHENTICATOR)
    if not runjsn:
      self.beamspot.pop((run,ls,le), None)
      return {}
    lsjsn   = fetch_data(datatype='lumisections' , dataid='_'.join([str(run), str(ls)]), omsapi=BSParser.AUTHENTICATOR)
    if not lsjsn:
      self.beamspot.pop((run,ls,le), None)
      return {}
    lejsn   = fetch_data(datatype='lumisections' , dataid='_'.join([str(run), str(le)]), omsapi=BSParser.AUTHENTICATOR) if le!=ls else lsjsn
    if not lejsn:
      self.beamspot.pop((run,ls,le), None)
      return {}
    filljsn = fetch_data(datatype='fills'        , dataid=runjsn['data']['attributes']['fill_number'], omsapi=BSParser.AUTHENTICATOR)
    if not filljsn:
      self.beamspot.pop((run,ls,le), None)
      return {}

    lumlist = [lsjsn]
    for l in range(ls+1,le):
      lj = fetch_data(datatype='lumisections', dataid='_'.join([str(run), str(l)]), omsapi=BSParser.AUTHENTICATOR)
      if lj:
        lumlist.append(lj)
    if le!=ls:
      lumlist.append(lejsn)

    with self.updatelock:
      if not (run,ls,le) in self.beamspot:
        self.beamspot[(run,ls,le)] = {}
      self.beamspot[(run,ls,le)]['fill'      ] = filljsn['data']['id']
      self.beamspot[(run,ls,le)]['run'       ] = runjsn ['data']['id']
      self.beamspot[(run,ls,le)]['fillstamp' ] = toepoch(filljsn['data']['attributes']['start_time'])
      self.beamspot[(run,ls,le)]['runstamp'  ] = toepoch(runjsn ['data']['attributes']['start_time'])
      self.beamspot[(run,ls,le)]['date'      ] = lsjsn['data']['attributes']['start_time'] 
      self.beamspot[(run,ls,le)]['IOVbegin'  ] = toepoch(lsjsn['data']['attributes']['start_time'])
      self.beamspot[(run,ls,le)]['IOVend'    ] = toepoch(lejsn['data']['attributes']['end_time'  ])
      self.beamspot[(run,ls,le)]['init_lumi' ] = sum(lum['data']['attributes']['init_lumi'] for lum in lumlist)/len(lumlist)  # 10^31 /s/cm^2
      self.beamspot[(run,ls,le)]['avg_pu'    ] = sum(lum['data']['attributes']['pileup']    for lum in lumlist)/len(lumlist)
      self.beamspot[(run,ls,le)]['timestamp' ] = 0.5*(
        toepoch(lejsn['data']['attributes']['end_time'  ]) +
        toepoch(lsjsn['data']['attributes']['start_time'])
      )
      self.beamspot[(run,ls,le)]['timewidth'] = (
        toepoch(lejsn['data']['attributes']['end_time'  ]) -
        toepoch(lsjsn['data']['attributes']['start_time'])
      )
      nlumis = runjsn['data']['attributes']['last_lumisection_number']
      nruns  = filljsn['data']['attributes']['last_run_number']-filljsn ['data']['attributes']['first_run_number']+1
      uniquerun  = float(runjsn ['data']['id'])+ls/nlumis
      uniquefill = float(filljsn['data']['id'])+uniquerun/nruns 
      self.beamspot[(run,ls,le)]['uniquerun']  = uniquerun
      self.beamspot[(run,ls,le)]['uniquefill'] = uniquefill

  @parallelize
  def _compute_proper_widths(self, runkey, approximate=True):
    ''' Rotate back the covariance matrix by -dx/dz and -dy/dz.
    The sigma_x and sigma_y *of the luminous region itself* are set.
    The dx/dy rotation is not corrected (but it's small).
    The effect on sigma_z is neglected as it's small.

    NOTE: the uncertainties for the non-approximated look wrong and anyway I am not sure why we should
    rotate the BS covariance matrix.
    '''
    # https://github.com/MilanoBicocca-pix/cmssw/blob/2d1e039a413496536abe6931561ea826025dc728/RecoVertex/BeamSpotProducer/src/PVFitter.cc#L302-L312
    # https://github.com/MilanoBicocca-pix/cmssw/blob/2d1e039a413496536abe6931561ea826025dc728/RecoVertex/BeamSpotProducer/src/PVFitter.cc#L241-L252
    widthXerr = self.beamspot[runkey]['covariance'][6][6]
    widthYerr = self.beamspot[runkey]['covariance'][7][7]
    widthZerr = self.beamspot[runkey]['covariance'][3][3]
    dxdzerr   = self.beamspot[runkey]['covariance'][4][4]
    dydzerr   = self.beamspot[runkey]['covariance'][5][5]
    XYerr     = self.beamspot[runkey]['covariance'][0][1]
    dxdz      = self.beamspot[runkey]['dxdz']
    dydz      = self.beamspot[runkey]['dydz']
    widthX    = self.beamspot[runkey]['widthX']
    widthY    = self.beamspot[runkey]['widthY']
    widthZ    = self.beamspot[runkey]['widthZ']

    alpha = unc.ufloat(-dydz, math.sqrt(dydzerr)) if not approximate else unc.ufloat(-dydz, 0.)
    beta  = unc.ufloat(-dxdz, math.sqrt(dxdzerr)) if not approximate else unc.ufloat(-dxdz, 0.)

    s_xx = unc.ufloat(np.power(widthX, 2), widthXerr) if not approximate else unc.ufloat(np.power(widthX, 2), 0.)
    s_yy = unc.ufloat(np.power(widthY, 2), widthYerr) if not approximate else unc.ufloat(np.power(widthY, 2), 0.)
    s_zz = unc.ufloat(np.power(widthZ, 2), widthZerr) if not approximate else unc.ufloat(np.power(widthZ, 2), 0.)
    # 100% uncertainty on XY correlation, as we don't save it...
    s_xz  = beta *(s_zz-s_xx)+alpha*unc.ufloat(XYerr, math.sqrt(abs(XYerr)))
    s_yz  = alpha*(s_yy-s_zz)-beta *unc.ufloat(XYerr, math.sqrt(abs(XYerr)))

    s_xx_true = s_xx-2.*beta *s_xz+np.power(beta , 2)*s_zz if not approximate else s_xx - beta*beta *s_zz
    s_yy_true = s_yy+2.*alpha*s_yz+np.power(alpha, 2)*s_zz if not approximate else s_yy - alpha*alpha*s_zz
    s_zz_true = s_zz

    with self.updatelock:
      self.beamspot[runkey]['widthXTrue'] = np.sqrt(max(0., s_xx_true.n))
      self.beamspot[runkey]['widthYTrue'] = np.sqrt(max(0., s_yy_true.n))
      self.beamspot[runkey]['widthZTrue'] = np.sqrt(max(0., s_zz_true.n))

      self.beamspot[runkey]['widthXTrueerr'] = np.sqrt(max(0., s_xx_true.s)) if not approximate else math.sqrt(max(0,s_xx_true.n)) * math.sqrt(max(0., widthXerr)) / max(1.e-12, widthX)
      self.beamspot[runkey]['widthYTrueerr'] = np.sqrt(max(0., s_yy_true.s)) if not approximate else math.sqrt(max(0,s_yy_true.n)) * math.sqrt(max(0., widthYerr)) / max(1.e-12, widthY)
      self.beamspot[runkey]['widthZTrueerr'] = np.sqrt(max(0., s_zz_true.s))

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
      beamspot = FormatInputTxt(ifile, fittype, flavour=flavour)
    return beamspot
  
  def writeTabularTxt(self, dirout):
    '''write a .txt beamspot file in tabular format
    '''
    os.makedirs(dirout, exist_ok=True)
    outputfile = self.filename.replace('.txt', '')
    FormatOutputTxt(self.beamspot, f'{dirout}/{outputfile}_default.txt', ispv=False)
    FormatOutputTxt(self.beamspot, f'{dirout}/{outputfile}_PV.txt', ispv=True)

    print(f"[INFO] fit info written to {outputfile}_default.txt in {dirout}")
    print(f"[INFO] fit info written to {outputfile}_PV.txt in {dirout}")
