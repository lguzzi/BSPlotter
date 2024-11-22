import ROOT
from BSLatex import BSLatex

class BSCanvas (ROOT.TCanvas):
  ''' class for handling the TCanvas style
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    ROOT.SetOwnership(self, False)
    self.SetGridx()
    self.SetGridy()
    self.SetBottomMargin(0.1)

class BSCanvasCMS(BSCanvas):
  ''' apply default CMS cosmetics to the canvas
  '''
  def __init__(self, **kwargs):
    super().__init__(kwargs.get('name', 'c1'),'',1420,335)
    self.SetTopMargin(0.10)
    self.SetLeftMargin(0.05)
    self.SetRightMargin(0.05)

    self.cmstext = BSLatex(self.GetRightMargin(), 1-0.9*self.GetTopMargin(), 'CMS ')
    self.cmstext.SetNDC()
    self.cmstext.SetTextFont(61)
    self.cmstext.SetTextSize(0.7*self.GetTopMargin())
    self.cmstext.SetTextAlign(11)
    self.extratext = BSLatex(self.GetRightMargin()+self.cmstext.GetXsize(), 1-0.9*self.GetTopMargin(), kwargs.get('extratext', ''))
    self.extratext.SetNDC()
    self.extratext.SetTextFont(52)
    self.extratext.SetTextSize(0.7*self.GetTopMargin()*0.9)
    self.extratext.SetTextAlign(11)
    self.lumitext = BSLatex(1-self.GetRightMargin(), 1-0.9*self.GetTopMargin(), kwargs.get('lumitext' , ''))
    self.lumitext.SetNDC()
    self.lumitext.SetTextFont(42)
    self.lumitext.SetTextSize(0.7*self.GetTopMargin()*0.9)
    self.lumitext.SetTextAlign(31)

  def SaveAs(self, *args, **kwargs):
    ''' this is needed for cosmetics to appear
    '''
    self.cmstext  .Draw()
    self.extratext.Draw()
    self.lumitext .Draw()
    super().SaveAs(*args, **kwargs)

  def Print(self, *args, **kwargs):
    ''' this is needed for cosmetics to appear
    '''
    self.cmstext  .Draw()
    self.extratext.Draw()
    self.lumitext .Draw()
    super().Print(*args, **kwargs)
