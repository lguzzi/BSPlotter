from cls.BSParser   import BSParser
from cls.BSPlotter  import BSPlotter
from cls.MPUtils    import MPManager

if __name__=='__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--input'   , required=True)
  parser.add_argument('--streams' , default=1, type=int)
  args = parser.parse_args()
  MPManager.THREADS = args.streams
  
  bsparser = BSParser(file=args.input)
  bsparser.fetch_from_OMS()
  bsplotter = BSPlotter(name='test', data=bsparser.beamspot)
  import pdb; pdb.set_trace()
