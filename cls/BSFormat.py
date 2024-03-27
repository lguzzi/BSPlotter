class BSFormat:
  ''' this class handles the format of the .txt file produced 
  by the BeamSpotProducer
  '''
  def __init__(self, file, canfail):
    self.file    = file
    self.canfail = canfail
  
  def get(self):
    self.data = {
      ( int(lines[self.run]              ), 
        int(lines[self.lumi].split(' ')[1]), 
        int(lines[self.lumi].split(' ')[3])): {
        'beginTime' : int   (lines[self.beginTime ] .split(' ')[-1]),
        'endTime'   : int   (lines[self.endTime   ] .split(' ')[-1]),
        'fittype'   : int   (lines[self.fittype   ] .split(' ')[-1]),
        'x'         : float (lines[self.x         ] .split(' ')[-1]),
        'y'         : float (lines[self.y         ] .split(' ')[-1]),
        'z'         : float (lines[self.z         ] .split(' ')[-1]),
        'widthZ'    : float (lines[self.widthZ    ] .split(' ')[-1]),
        'dxdz'      : float (lines[self.dxdz      ] .split(' ')[-1]),
        'dydz'      : float (lines[self.dydz      ].split(' ')[-1]),
        'widthX'    : float (lines[self.widthX    ].split(' ')[-1]),
        'widthY'    : float (lines[self.widthY    ].split(' ')[-1]),
        'emittanceX': float (lines[self.emittanceX].split(' ')[-1]),
        'emittanceY': float (lines[self.emittanceY].split(' ')[-1]),
        'betaStar'  : float (lines[self.betaStar  ].split(' ')[-1]),
        'covariance': [[float(e) for e in row.split(' ')[1:] if len(e)] for row in lines[self.covariance[0]:self.covariance[1]]],
      } for lines in [d.split('\n') for d in self.file.read().split(self.delimeter) if len(d)]
      if int(lines[4] .split(' ')[-1])==2 or self.canfail
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
    self.lumi       = 3
    self.endTime    = 2
    self.fittype    = 4
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
    self.fittype    = 4
    self.x          = 5
    self.y          = 6
    self.z          = 7
    self.widthZ     = 8
    self.dxdz       = 9
    self.dydz       = 10
    self.widthX     = 11
    self.widthY     = 12
    self.covariance = (13,20)
    self.emittanceX = 36
    self.emittanceY = 37
    self.betaStar   = 38
