import os, sys, math
sys.path.append('cls')
from MPUtils  import MPManager
from OMSUtils import fetch_data, get_authenticator
from datetime import datetime
from BSFormat import FormatInputTxt, FormatOutputTxt
import uncertainties as unc
import numpy as np

class BSParser:
  """Read beam-spot fits and enrich them with CMS OMS metadata.

  ``beamspot`` maps ``(run, lumi_start, lumi_end)`` tuples to fit values.
  OMS-derived fields such as timestamps, fill numbers, luminosity, and pileup
  are added by :meth:`fetch_timestamps_from_OMS`.

  ``DEBUG`` controls whether OMS requests are processed serially rather than
  through the multiprocessing pool.
  """
  MANAGER=MPManager()
  DEBUG=False
  AUTHENTICATOR=get_authenticator(verbose=DEBUG)

  def __init__(self, file, threads=1, flavour='default', fittype=2):
    """Load matching fits from ``file`` and prepare OMS access.

    Args:
      file: Path to a beam-spot fit-result text file.
      threads: Number of worker processes used for OMS lookups.
      flavour: Input layout, either ``'default'`` or ``'database'``.
      fittype: Fit status code to retain; defaults to successful fits (2).

    The input is parsed immediately. OMS metadata is fetched separately by
    calling :meth:`fetch_timestamps_from_OMS`.
    """
    # trigger the web authentication to avoid multiple authentications in parallel threads
    authenticate = fetch_data(datatype='runs', dataid=333333, omsapi=BSParser.AUTHENTICATOR)
    self.filename = os.path.basename(file)
    self.beamspot = BSParser.readTxtFile(file, fittype=fittype, flavour=flavour)
    self.threads  = threads
    self.flavour  = flavour

  def fetch_timestamps_from_OMS(self):
    """Fetch run, fill, and lumisection metadata for each parsed fit.

    Fits without matching OMS records are removed from ``self.beamspot``.
    Remaining records are enriched with timestamps, luminosity, pileup, and
    unique run/fill coordinates, then have their slope-corrected widths
    computed. Requests run in parallel unless ``BSParser.DEBUG`` is true.
    """
    print("[INFO] fetching data from OMS for", self.filename)
    fetched = BSParser.MANAGER.run_parallel(threads=self.threads,
      function=BSParser._fetch_timestamps_from_OMS,
      iterables=[(r,ls,le,len(self.beamspot.keys())) for (r,ls,le) in self.beamspot.keys()],
      debug=BSParser.DEBUG
    )
    fetched = {k:v for f in fetched for k,v in f.items() if f}
    self.beamspot = {k:v for k,v in self.beamspot.items() if k in fetched.keys()}
    for k in fetched.keys():
      self.beamspot[k] = {**self.beamspot[k],**fetched[k]}
      BSParser._compute_proper_widths(self.beamspot[k])

  @staticmethod
  def _fetch_timestamps_from_OMS(entry):
    """Fetch OMS metadata for one ``(run, lumi_start, lumi_end, total)`` job.

    This worker is an implementation detail used by
    :meth:`fetch_timestamps_from_OMS`; it returns an empty mapping when a
    required OMS record is unavailable.
    """
    run,ls,le,tot = entry
    toepoch = lambda tme: (datetime.strptime(tme, "%Y-%m-%dT%H:%M:%SZ")-datetime(1970,1,1)).total_seconds()
    runjsn  = fetch_data(datatype='runs'         , dataid=run, omsapi=BSParser.AUTHENTICATOR)
    if not runjsn:
      return {}
    lsjsn   = fetch_data(datatype='lumisections' , dataid='_'.join([str(run), str(ls)]), omsapi=BSParser.AUTHENTICATOR)
    if not lsjsn:
      return {}
    lejsn   = fetch_data(datatype='lumisections' , dataid='_'.join([str(run), str(le)]), omsapi=BSParser.AUTHENTICATOR) if le!=ls else lsjsn
    if not lejsn:
      return {}
    filljsn = fetch_data(datatype='fills'        , dataid=runjsn['data']['attributes']['fill_number'], omsapi=BSParser.AUTHENTICATOR)
    if not filljsn:
      return {}

    lumlist = [lsjsn]
    for l in range(ls+1,le):
      lum = fetch_data(datatype='lumisections', dataid='_'.join([str(run), str(l)]), omsapi=BSParser.AUTHENTICATOR)
      if lum:
        lumlist.append(lum)
    if le!=ls:
      lumlist.append(lejsn)

    beamspot = {}
    beamspot[(run,ls,le)] = {}
    beamspot[(run,ls,le)]['fill'      ] = filljsn['data']['id']
    beamspot[(run,ls,le)]['run'       ] = runjsn ['data']['id']
    beamspot[(run,ls,le)]['fillstamp' ] = toepoch(filljsn['data']['attributes']['start_time'])
    beamspot[(run,ls,le)]['runstamp'  ] = toepoch(runjsn ['data']['attributes']['start_time'])
    beamspot[(run,ls,le)]['date'      ] = lsjsn['data']['attributes']['start_time'] 
    beamspot[(run,ls,le)]['IOVbegin'  ] = toepoch(lsjsn['data']['attributes']['start_time'])
    beamspot[(run,ls,le)]['IOVend'    ] = toepoch(lsjsn['data']['attributes']['end_time'  ])
    beamspot[(run,ls,le)]['init_lumi' ] = sum(lum['data']['attributes']['init_lumi'] for lum in lumlist)/len(lumlist)  # 10^31 /s/cm^2
    beamspot[(run,ls,le)]['avg_pu'    ] = sum(lum['data']['attributes']['pileup']    for lum in lumlist)/len(lumlist)
    beamspot[(run,ls,le)]['timestamp' ] = 0.5*(
      toepoch(lejsn['data']['attributes']['end_time'  ]) +
      toepoch(lsjsn['data']['attributes']['start_time'])
    )
    beamspot[(run,ls,le)]['timewidth'] = (
      toepoch(lejsn['data']['attributes']['end_time'  ]) -
      toepoch(lsjsn['data']['attributes']['start_time'])
    )
    nlumis = runjsn['data']['attributes']['last_lumisection_number']
    nruns  = filljsn['data']['attributes']['last_run_number']-filljsn ['data']['attributes']['first_run_number']+1
    uniquerun  = float(runjsn ['data']['id'])+ls/nlumis
    uniquefill = float(filljsn['data']['id'])+uniquerun/nruns 
    beamspot[(run,ls,le)]['uniquerun']  = uniquerun
    beamspot[(run,ls,le)]['uniquefill'] = uniquefill
    BSParser.MANAGER.progress.value += 100./tot
    return beamspot

  @staticmethod
  def _compute_proper_widths(beamspot, approximate=True):
    """Add beam-slope-corrected widths to one parsed fit record.

    The values are stored as ``widthXTrue``, ``widthYTrue``, and
    ``widthZTrue`` with corresponding ``...err`` fields. With the default
    ``approximate=True``, uncertainties from the slopes and correlations are
    neglected; the correction to the z width is also neglected.

    This method mutates ``beamspot`` in place. The non-approximated
    uncertainty calculation is retained for comparison and is not the default.
    """
    # https://github.com/MilanoBicocca-pix/cmssw/blob/2d1e039a413496536abe6931561ea826025dc728/RecoVertex/BeamSpotProducer/src/PVFitter.cc#L302-L312
    # https://github.com/MilanoBicocca-pix/cmssw/blob/2d1e039a413496536abe6931561ea826025dc728/RecoVertex/BeamSpotProducer/src/PVFitter.cc#L241-L252
    widthXerr = beamspot['covariance'][6][6]
    widthYerr = beamspot['covariance'][7][7]
    widthZerr = beamspot['covariance'][3][3]
    dxdzerr   = beamspot['covariance'][4][4]
    dydzerr   = beamspot['covariance'][5][5]
    XYerr     = beamspot['covariance'][0][1]

    alpha = unc.ufloat(-beamspot['dydz'], math.sqrt(dydzerr)) if not approximate else unc.ufloat(-beamspot['dydz'], 0.)
    beta  = unc.ufloat(-beamspot['dxdz'], math.sqrt(dxdzerr)) if not approximate else unc.ufloat(-beamspot['dxdz'], 0.)

    s_xx = unc.ufloat(np.power(beamspot['widthX'], 2), widthXerr) if not approximate else unc.ufloat(np.power(beamspot['widthX'], 2), 0.)
    s_yy = unc.ufloat(np.power(beamspot['widthY'], 2), widthYerr) if not approximate else unc.ufloat(np.power(beamspot['widthY'], 2), 0.)
    s_zz = unc.ufloat(np.power(beamspot['widthZ'], 2), widthZerr) if not approximate else unc.ufloat(np.power(beamspot['widthZ'], 2), 0.)
    # 100% uncertainty on XY correlation, as we don't save it...
    s_xz  = beta *(s_zz-s_xx)+alpha*unc.ufloat(XYerr, math.sqrt(abs(XYerr)))
    s_yz  = alpha*(s_yy-s_zz)-beta *unc.ufloat(XYerr, math.sqrt(abs(XYerr)))

    s_xx_true = s_xx-2.*beta *s_xz+np.power(beta , 2)*s_zz if not approximate else s_xx - beta*beta *s_zz
    s_yy_true = s_yy+2.*alpha*s_yz+np.power(alpha, 2)*s_zz if not approximate else s_yy - alpha*alpha*s_zz
    s_zz_true = s_zz

    beamspot['widthXTrue'] = np.sqrt(max(0., s_xx_true.n))
    beamspot['widthYTrue'] = np.sqrt(max(0., s_yy_true.n))
    beamspot['widthZTrue'] = np.sqrt(max(0., s_zz_true.n))

    beamspot['widthXTrueerr'] = np.sqrt(max(0., s_xx_true.s)) if not approximate else math.sqrt(max(0,s_xx_true.n)) * math.sqrt(max(0., widthXerr)) / max(1.e-12, beamspot['widthX'])
    beamspot['widthYTrueerr'] = np.sqrt(max(0., s_yy_true.s)) if not approximate else math.sqrt(max(0,s_yy_true.n)) * math.sqrt(max(0., widthYerr)) / max(1.e-12, beamspot['widthY'])
    beamspot['widthZTrueerr'] = np.sqrt(max(0., s_zz_true.s))

  @staticmethod
  def readTxtFile(file, fittype=2, flavour='default'):
    """Read a fit-result file and return selected records.

    Args:
      file: Path to the input text file.
      fittype: Fit status code to keep.
      flavour: Input layout, either ``'default'`` or ``'database'``.

    Returns:
      A mapping from ``(run, lumi_start, lumi_end)`` tuples to fit-value
      dictionaries.
    """
    with open(file, 'r') as ifile:
      beamspot = FormatInputTxt(ifile, fittype, flavour=flavour)
    return beamspot
  
  def writeTabularTxt(self, dirout):
    """Write standard and PV tab-separated fit tables under ``dirout``.

    The output files are named ``<input-stem>_default.txt`` and
    ``<input-stem>_PV.txt``. The standard table reports unrotated
    laboratory-frame widths.
    """
    os.makedirs(dirout, exist_ok=True)
    outputfile = self.filename.replace('.txt', '')
    FormatOutputTxt(self.beamspot, f'{dirout}/{outputfile}_default.txt', ispv=False)
    FormatOutputTxt(self.beamspot, f'{dirout}/{outputfile}_PV.txt', ispv=True)

    print(f"[INFO] fit info written to {outputfile}_default.txt in {dirout}")
    print(f"[INFO] fit info written to {outputfile}_PV.txt in {dirout}")
