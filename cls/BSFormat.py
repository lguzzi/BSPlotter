from collections import OrderedDict
import os

class BSFormat:
  ''' this class handles the format of the .txt file produced 
  by the BeamSpotProducer
  '''
  def __init__(self, file, fittype=2):
    self.file    = file
    self.fittype = fittype
  
  def get(self):
    self.data = {
      ( int(lines[self.run]              ), 
        int(lines[self.lumi].split(' ')[1]), 
        int(lines[self.lumi].split(' ')[3])): {
        'runnumber' : int   (lines[self.run]                      ),
        'lumistart' : int   (lines[self.lumi].split(' ')[1]       ),
        'lumistop'  : int   (lines[self.lumi].split(' ')[3]       ),
        'beginTime' : int   (lines[self.beginTime ].split(' ')[-1]),
        'endTime'   : int   (lines[self.endTime   ].split(' ')[-1]),
        'fittype'   : int   (lines[self.fitresult ].split(' ')[-1]),
        'x'         : float (lines[self.x         ].split(' ')[-1]),
        'y'         : float (lines[self.y         ].split(' ')[-1]),
        'z'         : float (lines[self.z         ].split(' ')[-1]),
        'widthZ'    : float (lines[self.widthZ    ].split(' ')[-1]),
        'dxdz'      : float (lines[self.dxdz      ].split(' ')[-1]),
        'dydz'      : float (lines[self.dydz      ].split(' ')[-1]),
        'widthX'    : float (lines[self.widthX    ].split(' ')[-1]),
        'widthY'    : float (lines[self.widthY    ].split(' ')[-1]),
        'dxdy'      : float (lines[self.dxdy      ].split(' ')[-1]),
        'emittanceX': float (lines[self.emittanceX].split(' ')[-1]),
        'emittanceY': float (lines[self.emittanceY].split(' ')[-1]),
        'betaStar'  : float (lines[self.betaStar  ].split(' ')[-1]),
        'covariance': [[float(e) for e in row.split(' ')[1:] if len(e)] for row in lines[self.covariance[0]:self.covariance[1]+1]],
        'npvs'      : float (lines[self.npvs      ].split(' ')[-1]),
        'funcvalue' : float (lines[self.funcvalue ].split(' ')[-1]),
      } for lines in [d.split('\n') for d in self.file.read().split(self.delimeter) if len(d)]
      if int(lines[self.fitresult].split(' ')[-1])==self.fittype
    }
    return self.data

class BSFormatVanilla(BSFormat):
  ''' default .txt format
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.delimeter  = 'Runnumber '
    self.run        = 0
    self.beginTime  = 1
    self.endTime    = 2
    self.lumi       = 3
    self.fitresult  = 4
    self.x          = 5
    self.y          = 6
    self.z          = 7
    self.widthZ     = 8
    self.dxdz       = 9
    self.dydz       = 10
    self.widthX     = 11
    self.widthY     = 12
    self.covariance = (13,20)
    self.emittanceX = 20
    self.emittanceY = 21
    self.betaStar   = 22

class BSFormatVdM (BSFormat):
  ''' Van der Meer .txt format
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.delimeter  = 'Runnumber '
    self.run        = 0
    self.beginTime  = 1
    self.lumi       = 3
    self.endTime    = 2
    self.fitresult  = 4
    self.x          = 5
    self.y          = 6
    self.z          = 7
    self.widthZ     = 8
    self.dxdz       = 9
    self.dydz       = 10
    self.widthX     = 11
    self.widthY     = 12
    self.dxdy       = 13
    self.covariance = (14,22)
    self.emittanceX = 36
    self.emittanceY = 37
    self.betaStar   = 38
    self.npvs       = 39
    self.funcvalue  = 40

class BSFormatOut:
  ''' class to handle *output* .txt file formatting. WIP
  '''
  vdm = OrderedDict({
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
  def __init__(self, data, formatting):
    ''' takes data from the BSParser
    '''
    self.data = data
    self.form = formatting

  def write(self, filename):
    ''' write the .txt file with the specified format
    '''
    HEADERMAP = getattr(BSFormatOut, self.form)
    ROWSTRING = lambda bs:' \t'.join([str(getter(bs)) for _,getter in HEADERMAP.items()])
    with open(filename, 'w') as ofile:
      ofile.write(' \t'.join([k for k in HEADERMAP.keys()])+'\n')
      ofile.write('\n' .join([ROWSTRING(bs) for run,bs in self.data.items()])+'\n')
