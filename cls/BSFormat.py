from collections import OrderedDict
import os

def _fetcher_vdm(file, fittype):
  ''' fetcher for the default beamspot format
  '''
  grep = lambda txt, chunk, veto='margheritamiaquestaepurapoesiaeladedicoate': ([l for l in chunk if txt in l and not veto in l]+['missing -99'])[0]
  delimeter = 'Runnumber'
  return {
    ( int(chunk[0]                                ), 
      int(grep('LumiRange', chunk).split(' ')[-3] ),
      int(grep('LumiRange', chunk).split(' ')[-1] )): {
      'beginTime'   : int   (grep('BeginTimeOfFit', chunk               ).split(' ')[-1]),
      'endTime'     : int   (grep('EndTimeOfFit'  , chunk               ).split(' ')[-1]),
      'fittype'     : int   (grep('Type'          , chunk               ).split(' ')[-1]),
      'npvs'        : int   (grep('nPvs'          , chunk               ).split(' ')[-1]),
      'x'           : float (grep('X0'            , chunk, veto='xPV'   ).split(' ')[-1]),
      'y'           : float (grep('Y0'            , chunk, veto='yPV'   ).split(' ')[-1]),
      'z'           : float (grep('Z0'            , chunk               ).split(' ')[-1]),
      'widthZ'      : float (grep('sigmaZ0'       , chunk               ).split(' ')[-1]),
      'dxdz'        : float (grep('dxdz'          , chunk, veto='dxdzPV').split(' ')[-1]),
      'dydz'        : float (grep('dydz'          , chunk, veto='dydzPV').split(' ')[-1]),
      'widthX'      : float (grep('BeamWidthX'    , chunk               ).split(' ')[-1]),
      'widthY'      : float (grep('BeamWidthY'    , chunk               ).split(' ')[-1]),
      'dxdy'        : float (grep('dxdy'          , chunk               ).split(' ')[-1]),
      'emittanceX'  : float (grep('EmittanceX'    , chunk               ).split(' ')[-1]),
      'emittanceY'  : float (grep('EmittanceY'    , chunk               ).split(' ')[-1]),
      'betaStar'    : float (grep('BetaStar'      , chunk               ).split(' ')[-1]),
      'funcvalue'   : float (grep('funcValue'     , chunk               ).split(' ')[-1]),
      'covariance'  : [[float(e) for e in row.split(' ')[1:] if len(e)] for row in [grep('Cov({},j)'  .format(col), chunk, veto='PVCov') for col in range(9)]],
      'pvcovariance': [[float(e) for e in row.split(' ')[1:] if len(e)] for row in [grep('PVCov({},j)'.format(col), chunk              ) for col in range(9)]],
    } for chunk in [d.split('\n') for d in file.read().split(delimeter) if len(d)]
    if int(grep('Type', chunk).split(' ')[-1])==fittype
  }
def _fetcher_database(file, fittype):
  ''' fetcher for the database beamspot format
  '''
  grep = lambda txt, chunk, veto='margheritamiaquestaepurapoesiaeladedicoate': ([l for l in chunk if txt in l and not veto in l]+['missing -99'])[0]
  delimeter = 'for runs:'
  return {
    ( int(chunk[0].split(' ')[-3] ),
      int(chunk[0].split(' ')[-1] ),
      int(chunk[0].split(' ')[-1] )): {
      'fittype'     : int   (grep('Beam type'     , chunk               ).split(' ')[-1]),
      'x'           : float (grep('X0'            , chunk, veto='xPV'   ).split(' ')[-4]),
      'y'           : float (grep('Y0'            , chunk, veto='yPV'   ).split(' ')[-4]),
      'z'           : float (grep('Z0'            , chunk               ).split(' ')[-4]),
      'widthZ'      : float (grep('Sigma Z0'      , chunk               ).split(' ')[-4]),
      'dxdz'        : float (grep('dxdz'          , chunk, veto='dxdzPV').split(' ')[-4]),
      'dydz'        : float (grep('dydz'          , chunk, veto='dydzPV').split(' ')[-4]),
      'widthX'      : float (grep('Beam Width X'  , chunk               ).split(' ')[-4]),
      'widthY'      : float (grep('Beam Width Y'  , chunk               ).split(' ')[-4]),
      'emittanceX'  : float (grep('Emittance X'   , chunk               ).split(' ')[-2]),
      'emittanceY'  : float (grep('Emittance Y'   , chunk               ).split(' ')[-2]),
      'betaStar'    : float (grep('Beta star'     , chunk               ).split(' ')[-2]),
    } for chunk in [d.split('\n') for d in file.read().split(delimeter) if len(d)]
    if int(grep('Beam type', chunk).split(' ')[-1])==fittype
  }

def FormatInputTxt(file, fittype, flavour):
  ''' read the result of the beam analyzer and convert it into a dictionary.
  The grep veto is needed because some lines have similar names.
  '''
  fetcher = {
    'default' : _fetcher_vdm,
    'database': _fetcher_database,
  }[flavour]
  data = fetcher(file=file, fittype=fittype)
  return data

def FormatOutputTxt(self, data, filename):
  ''' write the .txt file with the specified format
  '''
  headermap = OrderedDict({
    'Runnumber':lambda dat:dat['runnumber'],
    'BeginTimeOfFit':lambda dat:dat['IOVbegin'],'EndTimeOfFit':lambda dat:dat['IOVend'],
    'Type':lambda dat:dat['fittype'],
    'X0':lambda dat:dat['x'],'Y0':lambda dat:dat['y'],'Z0':lambda dat:dat['z'],
    'sigmaZ0':lambda dat:dat['widthZ'],
    'dxdz':lambda dat:dat['dxdy'],'dydz':lambda dat:dat['dydz'],'dxdy':lambda dat:dat['dxdy'],
    'BeamWidthX':lambda dat:dat['widthX'],'BeamWidthY':lambda dat:dat['widthY'],
    'COV0,0':lambda dat:dat['covariance'][0][0],'COV0,1':lambda dat:dat['covariance'][0][1],'COV0,2':lambda dat:dat['covariance'][0][2],'COV0,3':lambda dat:dat['covariance'][0][3],'COV0,4':lambda dat:dat['covariance'][0][4],'COV0,5':lambda dat:dat['covariance'][0][5],'COV0,6':lambda dat:dat['covariance'][0][6],'COV0,7':lambda dat:dat['covariance'][0][7],'COV0,8':lambda dat:dat['covariance'][0][8],'COV1,0':lambda dat:dat['covariance'][1][0],'COV1,1':lambda dat:dat['covariance'][1][1],'COV1,2':lambda dat:dat['covariance'][1][2],'COV1,3':lambda dat:dat['covariance'][1][3],'COV1,4':lambda dat:dat['covariance'][1][4],'COV1,5':lambda dat:dat['covariance'][1][5],'COV1,6':lambda dat:dat['covariance'][1][6],'COV1,7':lambda dat:dat['covariance'][1][7],'COV1,8':lambda dat:dat['covariance'][1][8],'COV2,0':lambda dat:dat['covariance'][2][0],'COV2,1':lambda dat:dat['covariance'][2][1],'COV2,2':lambda dat:dat['covariance'][2][2],'COV2,3':lambda dat:dat['covariance'][2][3],'COV2,4':lambda dat:dat['covariance'][2][4],'COV2,5':lambda dat:dat['covariance'][2][5],'COV2,6':lambda dat:dat['covariance'][2][6],'COV2,7':lambda dat:dat['covariance'][2][7],'COV2,8':lambda dat:dat['covariance'][2][8],'COV3,0':lambda dat:dat['covariance'][3][0],'COV3,1':lambda dat:dat['covariance'][3][1],'COV3,2':lambda dat:dat['covariance'][3][2],'COV3,3':lambda dat:dat['covariance'][3][3],'COV3,4':lambda dat:dat['covariance'][3][4],'COV3,5':lambda dat:dat['covariance'][3][5],'COV3,6':lambda dat:dat['covariance'][3][6],'COV3,7':lambda dat:dat['covariance'][3][7],'COV3,8':lambda dat:dat['covariance'][3][8],'COV4,0':lambda dat:dat['covariance'][4][0],'COV4,1':lambda dat:dat['covariance'][4][1],'COV4,2':lambda dat:dat['covariance'][4][2],'COV4,3':lambda dat:dat['covariance'][4][3],'COV4,4':lambda dat:dat['covariance'][4][4],'COV4,5':lambda dat:dat['covariance'][4][5],'COV4,6':lambda dat:dat['covariance'][4][6],'COV4,7':lambda dat:dat['covariance'][4][7],'COV4,8':lambda dat:dat['covariance'][4][8],'COV5,0':lambda dat:dat['covariance'][5][0],'COV5,1':lambda dat:dat['covariance'][5][1],'COV5,2':lambda dat:dat['covariance'][5][2],'COV5,3':lambda dat:dat['covariance'][5][3],'COV5,4':lambda dat:dat['covariance'][5][4],'COV5,5':lambda dat:dat['covariance'][5][5],'COV5,6':lambda dat:dat['covariance'][5][6],'COV5,7':lambda dat:dat['covariance'][5][7],'COV5,8':lambda dat:dat['covariance'][5][8],'COV6,0':lambda dat:dat['covariance'][6][0],'COV6,1':lambda dat:dat['covariance'][6][1],'COV6,2':lambda dat:dat['covariance'][6][2],'COV6,3':lambda dat:dat['covariance'][6][3],'COV6,4':lambda dat:dat['covariance'][6][4],'COV6,5':lambda dat:dat['covariance'][6][5],'COV6,6':lambda dat:dat['covariance'][6][6],'COV6,7':lambda dat:dat['covariance'][6][7],'COV6,8':lambda dat:dat['covariance'][6][8],'COV7,0':lambda dat:dat['covariance'][7][0],'COV7,1':lambda dat:dat['covariance'][7][1],'COV7,2':lambda dat:dat['covariance'][7][2],'COV7,3':lambda dat:dat['covariance'][7][3],'COV7,4':lambda dat:dat['covariance'][7][4],'COV7,5':lambda dat:dat['covariance'][7][5],'COV7,6':lambda dat:dat['covariance'][7][6],'COV7,7':lambda dat:dat['covariance'][7][7],'COV7,8':lambda dat:dat['covariance'][7][8],'COV8,0':lambda dat:dat['covariance'][8][0],'COV8,1':lambda dat:dat['covariance'][8][1],'COV8,2':lambda dat:dat['covariance'][8][2],'COV8,3':lambda dat:dat['covariance'][8][3],'COV8,4':lambda dat:dat['covariance'][8][4],'COV8,5':lambda dat:dat['covariance'][8][5],'COV8,6':lambda dat:dat['covariance'][8][6],'COV8,7':lambda dat:dat['covariance'][8][7],'COV8,8':lambda dat:dat['covariance'][8][8],
    'nPVs':lambda dat:dat['npvs'],'FuncValue':lambda dat:dat['funcvalue'],
  })
  rowstring = lambda bs:' \t'.join([str(getter(bs)) for _,getter in headermap.items()])
  with open(filename, 'w') as ofile:
    ofile.write(' \t'.join([k for k in headermap.keys()])+'\n')
    ofile.write('\n' .join([rowstring(bs) for run,bs in data.items()])+'\n')
