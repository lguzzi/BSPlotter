from cls.BSParser   import BSParser
from cls.BSPlotter  import BSPlot1DByTime

if __name__=='__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--input'   , required=True)
  parser.add_argument('--output'  , required=True)
  parser.add_argument('--debug'   , action='store_true')
  parser.add_argument('--streams' , default=1, type=int)
  args = parser.parse_args()

  BSParser.DEBUG = args.debug
  # https://github.com/cms-sw/cmssw/blob/master/RecoVertex/BeamSpotProducer/src/BeamFitter.cc#L525-L533
  # https://github.com/cms-sw/cmssw/blob/4417f8d1645a31988011de3b45776241ca7708e0/DataFormats/BeamSpot/interface/BeamSpot.h#L24
  bssuccess     = BSParser(file=args.input, threads=args.streams, fittype=2)
  failedFake    = BSParser(file=args.input, threads=args.streams, fittype=0)
  failedUnknown = BSParser(file=args.input, threads=args.streams, fittype=-1)
  bssuccess     .fetch_timestamps_from_OMS() # good fits
  failedFake    .fetch_timestamps_from_OMS() # failed tracks fit
  failedUnknown .fetch_timestamps_from_OMS() # failed vertices fit
  failedMerged = {**failedUnknown.beamspot, **failedFake.beamspot}
  
  for plot in [BSPlot1DByTime(yvariable=y, ylabel=l, data=bssuccess.beamspot)
    for y,l in {
    'x'         : 'beam spot x [cm]'        ,
    'y'         : 'beam spot y [cm]'        ,
    'z'         : 'beam spot z [cm]'        ,
    'widthX'    : 'beam spot #sigma_x [cm]' ,
    'widthY'    : 'beam spot #sigma_y [cm]' ,
    'widthZ'    : 'beam spot #sigma_z [cm]' ,
    'dxdz'      : 'beam spot dx/dz'         ,
    'dydz'      : 'beam spot dy/dz'         ,
    'init_lumi' : 'luminosity at the beginning of the LS [10^{31} cm^{-2} s^{-1}]'
  }.items()]: plot.save(dirout=args.output)

  for plot in [BSPlot1DByTime(yvariable=y, ylabel=l, data=failedMerged)
    for y,l in {'init_lumi': 'luminosity at the beginning of the LS [10^{31} cm^{-2} s^{-1}]'}.items()
  ]: plot.save(dirout=args.output+'/failed')
