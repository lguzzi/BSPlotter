import ROOT
import os
from array    import array
from CMSStyle import CMS_lumi
from datetime import datetime
from BSGraph  import BSGraphByTime
from BSCanvas import BSCanvasCMS
from BSLine   import BSLineRun, BSLineFill
from BSLatex  import BSLatexRun, BSLatexFill, BSLatexRunOOR, BSLatexFillOOR
from datetime import datetime

ROOT.gROOT.SetBatch(True)

class BSPlotter:
  ''' base class to handle beam spot plot operations given 
  data from the BSParser
  '''
  TOPLOT  = {
    'x'     : 'beam spot x [cm]'        ,
    'y'     : 'beam spot y [cm]'        ,
    'z'     : 'beam spot z [cm]'        ,
    'widthX': 'beam spot #sigma_x [cm]' ,
    'widthY': 'beam spot #sigma_y [cm]' ,
    'widthZ': 'beam spot #sigma_z [cm]' ,
    'dxdz'  : 'beam spot dx/dz'         ,
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
    fills = set([(self.data[k]['fill'], self.data[k]['fillstamp']) for k in self.data.keys()])
    runs  = set([(self.data[k]['run' ], self.data[k]['runstamp' ]) for k in self.data.keys()])

    self.graphs = {
      v: BSGraphByTime(len(self.data.keys()),
        array('d', [bs['timestamp']  for bs in self.data.values()]),
        array('d', [bs[v]            for bs in self.data.values()]),
      ) 
      for v in BSPlotter.TOPLOT.keys()
    }
    self.cosmetics = {}
    for v, g in self.graphs.items():
      g.SetTitle(';{X};{Y}'.format(X='date (UTC)', Y=BSPlotter.TOPLOT[v]))
      ymin = g.GetYaxis().GetXmin()
      ymax = g.GetYaxis().GetXmax()
      xmin = g.GetXaxis().GetXmin()
      xmax = g.GetXaxis().GetXmax()
      self.cosmetics[v] = [
        BSLineFill (t, ymin, t, ymax) for f, t in fills if xmin < t < xmax ]+[
        BSLineRun  (t, ymin, t, ymax) for r, t in runs  if xmin < t < xmax ]+[
        BSLatexFill(t+0.01*(xmax-xmin), ymax-0.2*(ymax-ymin), f) if xmin < t < xmax else BSLatexFillOOR(xmin+0.01*(xmax-xmin), ymax-0.05*(ymax-ymin), "since fill " +f) for f, t in fills]+[
        BSLatexRun (t+0.01*(xmax-xmin), ymax-0.2*(ymax-ymin), r) if xmin < t < xmax else BSLatexRunOOR (xmin+0.01*(xmax-xmin), ymax-0.10*(ymax-ymin), "since run "  +r) for r, t in runs ]

  def save(self, dirout):
    os.makedirs(dirout, exist_ok=True)
    can = BSCanvasCMS(lumitext="13.6 TeV", extratext='Internal')
    for v, g in self.graphs.items():
      g.Draw("AP SAME")
      for c in self.cosmetics[v]:
        c.Draw("SAME")
      can.SaveAs(dirout+'/'+v+'.pdf', 'pdf')
      can.SaveAs(dirout+'/'+v+'.png', 'png')
