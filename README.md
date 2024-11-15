Run/Fill/Lumisection metadata are fetched on-the-fly from [OMS](https://cmsoms.cern.ch/) using the [OMS API library](https://gitlab.cern.ch/cmsoms/oms-api-client). An OMS authenticator will be created on-the-fly using kerberos. [tsgauth](https://pypi.org/project/tsgauth/) must be installed.
Command example:
```bash
kinit
python3 plotter.py --input BSFit_VdM2023_partial.txt --streams 1 --flavour vdm
```
