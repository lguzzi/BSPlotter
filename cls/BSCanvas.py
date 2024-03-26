import ROOT
from CMSStyle import CMS_lumi

class BSCanvas (ROOT.TCanvas):
  ''' class for handling the TCanvas style
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.SetGridx()
    self.SetGridy()
    self.SetBottomMargin(0.1)
    self.SetGridy()

class BSCanvasCMS(BSCanvas):
  ''' apply the CMSStyle to the canvas as from
  CMSStyle.py
  '''
  def __init__(self, lumiText):
    super().__init__('c1','',1420,335)
    CMS_lumi(self, lumiText=lumiText)