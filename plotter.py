from cls.BSParser   import BSParser
from cls.BSPlotter  import BSPlotter

if __name__=='__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--input', required=True)
  args = parser.parse_args()
  bsparser = BSParser(file=args.input)
  bsparser.fetch_from_OMS()
  bsplotter = BSPlotter(name='test', data=bsparser.beamspot)
  import pdb; pdb.set_trace()
