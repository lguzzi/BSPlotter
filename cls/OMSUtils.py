import importlib
OMSAPI = importlib.import_module("oms-api-client.omsapi").OMSAPI

def fetch_data(datatype, dataid, authentication='auth_device', verbose=False):
  ''' fetch data from an OMS url using the official OMS API interface https://gitlab.cern.ch/cmsoms/oms-api-client
  '''
  omsapi = OMSAPI("https://cmsoms.cern.ch/agg/api", "v1", cert_verify=False, verbose=verbose)
  getattr(omsapi, authentication)()
  query     = omsapi.query('/'.join([datatype, str(dataid)]))
  response  = query.data()
  return response.json() if response.ok else {}
