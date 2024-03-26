from cls.BSParser   import BSParser
from cls.BSPlotter  import BSPlotterByTime
from cls.MPUtils    import MPManager

if __name__=='__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--input'   , required=True)
  parser.add_argument('--streams' , default=1, type=int)
  parser.add_argument('--flavour' , default='default', help='set to \'vdm\' if the output formatting is vdm-like (contains the PV cov. matrix)')
  args = parser.parse_args()
  
  bsparser = BSParser(file=args.input, threads=args.streams, flavour=args.flavour)
  bsparser.fetch_from_OMS()
  bsplotter = BSPlotterByTime(name='test', data=bsparser.beamspot)
  bsplotter.save("test")
  import pdb; pdb.set_trace()
