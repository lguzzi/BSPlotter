import importlib
OMSAPI = importlib.import_module("oms-api-client.omsapi").OMSAPI

def get_authenticator(authentication='auth_device', verbose=False):
  omsapi =  OMSAPI("https://cmsoms.cern.ch/agg/api", "v1", cert_verify=False, verbose=verbose)
  getattr(omsapi, authentication)()
  return omsapi

def fetch_data(datatype, dataid, omsapi):
  ''' fetch data from an OMS url using the official OMS API interface https://gitlab.cern.ch/cmsoms/oms-api-client
  '''
  query = omsapi.query('/'.join([datatype, str(dataid)]))
  i=0
  response = query.data()
  while i<5 and not response.ok:
    response = query.data()
    i=i+1
  return response.json() if response.ok else {}
