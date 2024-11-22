This repository is used to manipulate beamspot fit results.  

# installation
The environment manager [mamba](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html) is required.  
The required packages are listed in [environment.yaml](environment.yaml):
```bash
mamba env create -f environment.yaml
mamba activate beamspot
```

**NOTE:** root=6.30.4 is needed, <ins>not newer</ins>, due to [this problem](https://root-forum.cern.ch/t/typeerror-no-python-side-overrides-supported-failed-to-compile-the-dispatcher-code/53198/20).

# parsing
[BSParser.py](cls/BSParser.py) contains the BSParser class, responsible for parsing the result of [BeamAnalyzer.cc]() and fetching the needed information from OMS.  
Run/Fill/Lumisection data is fetched on-the-fly from [OMS](https://cmsoms.cern.ch/) using the [OMS API library](https://gitlab.cern.ch/cmsoms/oms-api-client). An OMS authenticator will be created on-the-fly using kerberos. [tsgauth](https://pypi.org/project/tsgauth/) must be installed.  
The parsing object takes a *.txt* file as input (the result of the beamspot fit) and a fit type indicating the status of the fit as described in the source code [1][2] (by default, only converging fits are selected and the default fit type value is *2*).  
The parser can work in parallel over the (run, lumi_start, lumi_end) list, debugging can be enabled setting ```BSParser.DEBUG=True```.  

[1] https://github.com/cms-sw/cmssw/blob/master/RecoVertex/BeamSpotProducer/src/BeamFitter.cc#L525-L533  
[2] https://github.com/cms-sw/cmssw/blob/4417f8d1645a31988011de3b45776241ca7708e0/DataFormats/BeamSpot/interface/BeamSpot.h#L24  

# plotting
Plotting is handled by the [BSPlotter.py](cls/BSPlotter.py) objects. The needed inputs are the *y* variable and its title, and the beamspot dictionary as defined in the BSParser class. Different subclasses implement different cosmetics (additional informations added to the plot).  

# general
Multiple ROOT classes are re-defined in the [cls](cls) folder in order to facilitate the handling of cosmetic objects.  

An example of use is shown in [plotter.py](plotter.py):

```bash
python3 plotter.py --streams 15 --input input.txt --output test
```
