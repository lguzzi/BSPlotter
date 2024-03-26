import ROOT

# CMS_lumi
#   Initiated by: Gautier Hamel de Monchenault (Saclay)
#   Translated in Python by: Joshua Hardenbrook (Princeton)

def CMS_lumi(pad, lumiText, 
iPosX                 = 10            ,
cmsText               = "CMS"         ,
cmsTextFont           = 61            ,
writeExtraText        = True          ,
extraText             = "Preliminary" ,
extraTextFont         = 52            ,
lumiTextSize          = 0.5           ,
lumiTextOffset        = 0.2           ,
cmsTextSize           = 0.7           ,
cmsTextOffset         = 0.1           ,
relPosX               = 0.070         ,
relPosY               = 0.025         ,
relExtraDY            = 1.2           ,
extraOverCmsTextSize  = 0.8           ,
drawLogo              = False         ,
):
  outOfFrame = iPosX==0

  alignX_ = 1 if iPosX==0 or iPosX==10 else 3 if iPosX==30 else 2
  alignY_ = 1 if iPosX==0 else 3
  align_  = 10*alignX_+alignY_

  H = pad.GetWh()
  W = pad.GetWw()
  l = pad.GetLeftMargin()
  t = pad.GetTopMargin()
  r = pad.GetRightMargin()
  b = pad.GetBottomMargin()
  e = 0.025
  
  pad.cd()

  latex = ROOT.TLatex()
  latex.SetNDC()
  latex.SetTextAngle(0)
  latex.SetTextColor(1)    
  latex.SetTextFont(42)
  latex.SetTextAlign(31) 
  latex.SetTextSize(lumiTextSize*t)    
  latex.DrawLatex(1-r,1-t+lumiTextOffset*t,lumiText)
  if outOfFrame:
    latex.SetTextFont(cmsTextFont)
    latex.SetTextAlign(11) 
    latex.SetTextSize(cmsTextSize*t)    
    latex.DrawLatex(l,1-t+lumiTextOffset*t,cmsText)

  extraTextSize = extraOverCmsTextSize*cmsTextSize

  posX_ = l+relPosX*(1-l-r)   if iPosX%10<=1 else \
          l+0.5*(1-l-r)       if iPosX%10==2 else \
          1-r-relPosX*(1-l-r) if iPosX%10==3 else 0
  posY_ = 1-t-relPosY*(1-t-b)

  if not outOfFrame:
    if drawLogo:
      posX_ = l+0.045*(1-l-r)*W/H
      posY_ = 1-t-0.045*(1-t-b)
      CMS_logo = ROOT.TASImage("CMS-BW-label.png")
      pad_logo = ROOT.TPad("logo","logo", posX_, posY_-0.15, posX_+0.15*H/W, posY_)
      pad_logo.Draw()
      pad_logo.cd()
      CMS_logo.Draw("X")
      pad_logo.Modified()
      pad.cd()
    else:
      latex.SetTextFont(cmsTextFont)
      latex.SetTextSize(cmsTextSize*t)
      latex.SetTextAlign(align_)
      latex.DrawLatex(posX_, posY_, cmsText)
      if writeExtraText:
        latex.SetTextFont(extraTextFont)
        latex.SetTextAlign(align_)
        latex.SetTextSize(extraTextSize*t)
        latex.DrawLatex(posX_, posY_- relExtraDY*cmsTextSize*t, extraText)
  elif writeExtraText:
    if iPosX==0:
      posX_ = l+relPosX*(1-l-r)
      posY_ = 1-t+lumiTextOffset*t
    latex.SetTextFont(extraTextFont)
    latex.SetTextSize(extraTextSize*t)
    latex.SetTextAlign(align_)
    latex.DrawLatex(posX_, posY_, extraText)      

  pad.Update()
