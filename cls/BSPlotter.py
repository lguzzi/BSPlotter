import ROOT
import os
from array    import array
from datetime import datetime
from BSGraph  import BSGraph, BSGraphByTime
from BSCanvas import BSCanvasCMS
from BSLine   import BSLineRun, BSLineFill
from BSLatex  import BSLatexRun, BSLatexFill, BSLatexRunOOR, BSLatexFillOOR
from datetime import datetime

ROOT.gROOT.SetBatch(True)

class BSPlot1D:
  """Base class for plotting one field from a beam-spot record mapping.

  Subclasses choose the x-axis field and graph type. ``data`` is the mapping
  produced by :class:`BSParser`; ``yvariable`` names a field in each record.
  """
  def __init__(self, yvariable, ylabel, data, xvariable, xlabel):
    """Configure a plot from data fields and axis labels."""
    self.yvar = yvariable
    self.xvar = xvariable
    self.ylab = ylabel
    self.xlab = xlabel
    self.data = data
    self.cosmetics = []

  def add_cosmetics(self):
    """Populate plot-specific annotations, such as run and fill markers."""
    return

  def save(self, dirout):
    """Draw the graph and save PDF and PNG files in ``dirout``.

    The output files are named after ``yvariable``. Plot-specific annotations
    are added immediately before drawing.
    """
    self.add_cosmetics()
    os.makedirs(dirout, exist_ok=True)
    can = BSCanvasCMS(name=self.yvar+'can', lumitext="13.6 TeV", extratext='Internal')
    self.plot.Draw("AP")
    for c in self.cosmetics:
      c.Draw("SAME")
    can.SaveAs(dirout+'/'+self.yvar+'.pdf', 'pdf')
    can.SaveAs(dirout+'/'+self.yvar+'.png', 'png')

class BSPlot1DByFill(BSPlot1D):
  """Plot a beam-spot field against the unique fill coordinate.

  Requires OMS-enriched records containing ``uniquefill``.
  """
  def __init__(self, *args, **kwargs):
    kwargs.update({'xvariable':'uniquefill', 'xlabel':'fill number'})
    super().__init__(*args, **kwargs)
    self.plot = BSGraph(len(self.data.keys()),
      array('d', [bs[self.xvar] for bs in self.data.values()]),
      array('d', [bs[self.yvar] for bs in self.data.values()]),
    )
    self.plot.SetTitle(';{X};{Y}'.format(X=self.xlab, Y=self.ylab))

class BSPlot1DByRun(BSPlot1D):
  """Plot a beam-spot field against the unique run coordinate.

  Requires OMS-enriched records containing ``uniquerun``, ``fill``,
  ``fillstamp``, and ``runstamp``.
  """
  def __init__(self, *args, **kwargs):
    kwargs.update({'xvariable':'uniquerun', 'xlabel':'run number'})
    super().__init__(*args, **kwargs)
    self.plot = BSGraph(len(self.data.keys()),
      array('d', [bs[self.xvar] for bs in self.data.values()]),
      array('d', [bs[self.yvar] for bs in self.data.values()]),
    )
    self.plot.SetTitle(';{X};{Y}'.format(X=self.xlab, Y=self.ylab))

  def add_cosmetics(self):
    ymin = self.plot.GetYaxis().GetXmin()
    ymax = self.plot.GetYaxis().GetXmax()
    xmin = self.plot.GetXaxis().GetXmin()
    xmax = self.plot.GetXaxis().GetXmax()
    fills = set([(self.data[k]['fill'], self.data[k]['fillstamp']) for k in self.data.keys()])
    self.cosmetics = [
      BSLineFill (t, ymin, t, ymax) for f, t in fills if xmin < t < xmax ]+[
      BSLatexFill(t+0.01*(xmax-xmin), ymax-0.2*(ymax-ymin), f) if xmin < t < xmax else BSLatexFillOOR(xmin+0.01*(xmax-xmin), ymax-0.05*(ymax-ymin), "since fill " +f) for f, t in fills]

class BSPlot1DByTime(BSPlot1D):
  """Plot a beam-spot field against its OMS timestamp.

  Requires OMS-enriched records containing ``timestamp``, ``fill``,
  ``fillstamp``, ``run``, and ``runstamp``.
  """
  def __init__(self, *args, **kwargs):
    kwargs.update({'xvariable':'timestamp', 'xlabel':'date (UTC)'})
    super().__init__(*args, **kwargs)
    self.plot = BSGraphByTime(len(self.data.keys()),
      array('d', [bs[self.xvar] for bs in self.data.values()]),
      array('d', [bs[self.yvar] for bs in self.data.values()]),
    )
    self.plot.SetTitle(';{X};{Y}'.format(X=self.xlab, Y=self.ylab))

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
  """Draw multiple configured plot graphs together on one canvas.

  Args:
    plots: Non-empty sequence of plot objects with compatible axes.
    output: Directory in which the canvas is saved.
  """
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

def multiaxes(left, right, output):
  """Draw several plots with shared x and separate left/right y axes.

  Args:
    left: Non-empty sequence of plot objects for the left y-axis.
    right: Optional sequence of plot objects for the right y-axis.
    output: Directory in which PDF and PNG canvases are saved.
  """
  os.makedirs(output, exist_ok=True)
  can = BSCanvasCMS(lumitext="13.6 TeV", extratext='Internal')
  cosmetics = left[0].cosmetics
  multigraph = ROOT.TMultiGraph()
  for i, p in enumerate(left):
    p.plot.SetLineColor(i+1)
    p.plot.SetMarkerColor(i+1)
    p.plot.SetMarkerStyle(i+20)
    multigraph.Add(p.plot)
  multigraph.SetNameTitle(left[0].yvar+'multig', ';{};{}'.format(left[0].xvar, left[0].yvar))
  
  if len(right):
    right_axis = right[0].plot.GetYaxis()
    right_axis.SetLabelColor(right[0].plot.GetLineColor())
    right_axis.SetTitleColor(right[0].plot.GetLineColor())
  for p in right:
    scale_factor = (multigraph.GetYaxis().GetXmax() - multigraph.GetYaxis().GetXmin()) / (p.plot.GetYaxis().GetXmax() - p.plot.GetYaxis().GetXmin())
    p.plot.Scale(scale_factor)
  
  ROOT.SetOwnership(multigraph, False)
  multigraph.Draw('AP')
  if len(right):
    right_axis.Draw()

  for c in cosmetics:
    c.Draw("SAME")
  can.SaveAs('{}/{}.pdf'.format(output, left[0].yvar), 'pdf')
  can.SaveAs('{}/{}.png'.format(output, left[0].yvar), 'png')
