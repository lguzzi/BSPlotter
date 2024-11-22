import ROOT
import os
from array    import array
from datetime import datetime
from BSGraph  import BSGraphByTime
from BSCanvas import BSCanvasCMS
from BSLine   import BSLineRun, BSLineFill
from BSLatex  import BSLatexRun, BSLatexFill, BSLatexRunOOR, BSLatexFillOOR
from datetime import datetime

ROOT.gROOT.SetBatch(True)

class BSPlot1D:
  ''' virtual class for plotting a 1D graph from a beamspot dictionary
  '''
  def __init__(self, yvariable, ylabel, data):
    self.xvar = None
    self.yvar = yvariable
    self.ylab = ylabel
    self.data = data
    self.cosmetics = []

  def add_cosmetics(self):
    ''' cosmetics are additional informations such as run/fill numbers, specific of the type of plot
    '''
    return

  def save(self, dirout):
    self.add_cosmetics()
    os.makedirs(dirout, exist_ok=True)
    can = BSCanvasCMS(name=self.yvar+'can', lumitext="13.6 TeV", extratext='Internal')
    self.plot.Draw("AP")
    for c in self.cosmetics:
      c.Draw("SAME")
    can.SaveAs(dirout+'/'+self.yvar+'.pdf', 'pdf')
    can.SaveAs(dirout+'/'+self.yvar+'.png', 'png')

class BSPlot1DByTime(BSPlot1D):
  ''' base class for plotting a 1D graph from a beamspot dictionary vs. time
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.xvar = 'timestamp'
    self.plot = BSGraphByTime(len(self.data.keys()),
      array('d', [bs[self.xvar] for bs in self.data.values()]),
      array('d', [bs[self.yvar] for bs in self.data.values()]),
    )
    self.plot.SetTitle(';{X};{Y}'.format(X='date (UTC)', Y=self.ylab))

  def add_cosmetics(self):
    ymin = self.plot.GetYaxis().GetXmin()
    ymax = self.plot.GetYaxis().GetXmax()
    xmin = self.plot.GetXaxis().GetXmin()
    xmax = self.plot.GetXaxis().GetXmax()
    fills = set([(self.data[k]['fill'], self.data[k]['fillstamp']) for k in self.data.keys()])
    runs  = set([(self.data[k]['run' ], self.data[k]['runstamp' ]) for k in self.data.keys()])
    self.cosmetics = [
      BSLineFill (t, ymin, t, ymax) for f, t in fills if xmin < t < xmax ]+[
      BSLineRun  (t, ymin, t, ymax) for r, t in runs  if xmin < t < xmax ]+[
      BSLatexFill(t+0.01*(xmax-xmin), ymax-0.2*(ymax-ymin), f) if xmin < t < xmax else BSLatexFillOOR(xmin+0.01*(xmax-xmin), ymax-0.05*(ymax-ymin), "since fill " +f) for f, t in fills]+[
      BSLatexRun (t+0.01*(xmax-xmin), ymax-0.2*(ymax-ymin), r) if xmin < t < xmax else BSLatexRunOOR (xmin+0.01*(xmax-xmin), ymax-0.10*(ymax-ymin), "since run "  +r) for r, t in runs ]

def multiplot(plots, output):
  ''' helper function for plotting multiple BSPlot1D on the same canvas
  '''
  os.makedirs(output, exist_ok=True)
  can = BSCanvasCMS(lumitext="13.6 TeV", extratext='Internal')
  cosmetics = plots[0].cosmetics
  leg = ROOT.TLegend()
  multigraph = ROOT.TMultiGraph()
  for i, p in enumerate(plots):
    p.plot.SetLineColor(i+1)
    p.plot.SetMarkerColor(i+1)
    p.plot.SetMarkerStyle(i+20)
    leg.AddEntry(p.plot, p.name, 'lp')
    multigraph.Add(p.plot)
  multigraph.SetNameTitle(plots[0].yvar+'multig', ';{};{}'.format(plots[0].xvar, plots[0].yvar))
  ROOT.SetOwnership(multigraph, False)
  multigraph.Draw('AP')
  for c in cosmetics:
    c.Draw("SAME")
  leg.Draw()
  can.SaveAs('{}/{}.pdf'.format(output, var), 'pdf')
  can.SaveAs('{}/{}.png'.format(output, var), 'png')
