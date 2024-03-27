import ROOT
class BSGraph(ROOT.TGraph):
  ''' class for handling the TGraph style
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.SetMarkerStyle(8)
    self.SetMarkerSize(0.3)
    self.SetLineColor(ROOT.kBlack)
    self.SetMarkerColor(ROOT.kBlack)
    self.GetYaxis().SetTitleOffset(1.5)

class BSGraphByTime(BSGraph):
  TIMEFORMAT  = '%Y-%m-%d %H:%M'
  def __init__(self, *args, **kwargs):
    ''' class for handling TGraph with datetime
    x-axis
    '''
    super().__init__(*args, **kwargs)
    self.GetXaxis().SetTimeDisplay(True)
    self.GetXaxis().SetTimeOffset(0, 'utc')
    self.GetXaxis().SetTimeFormat(BSGraphByTime.TIMEFORMAT)
