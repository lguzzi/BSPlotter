import ROOT

class BSLatex (ROOT.TLatex):
  ''' class for handling the TLatex style. The drawn text is passed as the 
  object name for simplicity.
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
  
  def Draw(self, *args, **kwargs):
    '''The plot attributes are declared in the constructor, 
    the DrawLatex function relies on the class attributes
    '''
    self.DrawLatex(self.GetX(), self.GetY(), self.GetTitle())

class BSLatexRun(BSLatex):
  ''' write run number on the canvas
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.SetTextSize(0.04)
    self.SetTextColorAlpha(ROOT.kBlue, 1.0)
    self.SetTextAngle(90)

class BSLatexRunOOR(BSLatexRun):
  ''' write run number on the canvas for out of range runs
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.SetTextAngle(0)

class BSLatexFill(BSLatex):
  ''' write fill number on the canvas
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.SetTextSize(0.04)
    self.SetTextColorAlpha(ROOT.kRed, 1.0)
    self.SetTextAngle(90)

class BSLatexFillOOR(BSLatexFill):
  ''' write run number on the canvas for out of range fills
  '''
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.SetTextAngle(0)