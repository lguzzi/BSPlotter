import ROOT
class BSLine (ROOT.TLine):
  ''' class for handling the TLine style
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class BSLineRun (BSLine):
  ''' class for handling TLine objects
  for plotting vertical run number separators
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.SetLineColor(ROOT.kBlue)
    self.SetLineWidth(1)

class BSLineFill (BSLine):
  ''' class for handling TLine objects
  for plotting vertical fill number separators
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.SetLineColorAlpha(ROOT.kRed, 0.5)
    self.SetLineWidth(2)
