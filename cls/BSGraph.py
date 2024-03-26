import ROOT
from datetime import datetime
class BSGraph (ROOT.TGraph):
  ''' class for handling the TGraph style
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.SetMarkerStyle(8)
    self.SetMarkerSize(0.3)
    self.SetLineColor(ROOT.kBlack)
    self.SetMarkerColor(ROOT.kBlack)
    self.GetYaxis().SetTitleOffset(1.5)

class BSGraphByTime (BSGraph):
  TIMEFORMAT  = '%Y-%m-%d %H:%M'
  TIMESTEP    = 60*60*6
  def __init__(self, *args, **kwargs):
    ''' class for handling TGraph with datetime
    x-axis
    '''
    super().__init__(*args, **kwargs)

    for n in range(1, self.GetN()+1):
      self.GetXaxis().SetBinLabel(
        n, datetime.fromtimestamp(self.GetXaxis().GetBinCenter(n)).strftime(BSGraphByTime.TIMEFORMAT)
      )
