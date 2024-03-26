import ROOT
import os
from array    import array
from CMSStyle import CMS_lumi
from datetime import datetime
from BSGraph  import BSGraphByTime
from BSCanvas import BSCanvasCMS
from datetime import datetime

ROOT.gROOT.SetBatch(True)

class BSPlotter:
  ''' base class to handle beam spot plot operations given 
  data from the BSParser
  '''
  TOPLOT  = {
    'x'     : 'beam spot x [cm]'      ,
    'y'     : 'beam spot y [cm]'      ,
    'z'     : 'beam spot z [cm]'      ,
    'widthX': 'beam spot #sigma_x [cm]',
    'widthY': 'beam spot #sigma_y [cm]',
    'widthZ': 'beam spot #sigma_z [cm]',
    'dxdz'  : 'beam spot dx/dz'       ,
    'dydz'  : 'beam spot dy/dz'
  }
  def __init__(self, name, data):
    self.data = data
    self.name = name

class BSPlotterByTime(BSPlotter):
  ''' handles plots by time (aka lumisections)
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.graphs = {
      v: BSGraphByTime(len(self.data.keys()),
        array('d', [bs['timestamp']  for bs in self.data.values()]),
        array('d', [bs[v]            for bs in self.data.values()]),
      ) 
      for v in BSPlotter.TOPLOT.keys()
    }
    for v, g in self.graphs.items():
      g.SetTitle(';{X};{Y}'.format(X='date', Y=BSPlotter.TOPLOT[v]))
    for g in self.graphs.values():
      dates = BSPlotterByTime.nicetimestamp([_ for _ in g.GetX()])
      for i,d in enumerate(dates):
        g.GetXaxis().SetBinLabel(i+1, d)

  def save(self, dirout):
    os.makedirs(dirout, exist_ok=True)
    can = BSCanvasCMS(lumiText="13.6 TeV")
    for v, g in self.graphs.items():
      g.Draw("AP")
      can.SaveAs(dirout+'/'+v+'.pdf', 'pdf')
  
  @staticmethod
  def nicetimestamp(timestamps, period=10):
    ''' convert a timestamp every period to a date string
    '''
    return [str(datetime.fromtimestamp(int(d))) if not i%int(len(timestamps)//period) else '' 
      for i,d in enumerate(timestamps)
    ]

