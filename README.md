Run/Fill/Lumisection metadata are fetched on-the-fly from [OMS](https://cmsoms.cern.ch/). An OMS cookie file will be created using kerberos. [auth-get-sso-cookie](https://auth.docs.cern.ch/applications/command-line-tools/#auth-get-sso-cookie) must be installed.
Command example:
```bash
kinit
python3 plotter.py --input BSFit_VdM2023_partial.txt --streams 1 --flavour vdm
```
