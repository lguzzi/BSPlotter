import ROOT
class BSGraph(ROOT.TGraph):
  ''' class for handling the TGraph style
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.SetMarkerStyle(8)
    self.SetMarkerSize(0.3)
    self.SetLineColor(ROOT.kRed)
    self.SetMarkerColor(ROOT.kRed)
    self.GetYaxis().SetTitleOffset(0.7)

class BSGraphByTime(BSGraph):
  TIMEFORMAT  = '%Y-%m-%d %H:%M'
  def __init__(self, *args, **kwargs):
    ''' class for handling TGraph with datetime
    x-axis
    '''
    super().__init__(*args, **kwargs)
    self.GetXaxis().SetTimeDisplay(True)
    self.GetXaxis().SetTimeOffset(0, 'gmt')
    self.GetXaxis().SetTimeFormat(BSGraphByTime.TIMEFORMAT)
