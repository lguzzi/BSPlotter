import importlib
from omsapi import OMSAPI

def get_authenticator(authentication='auth_device', verbose=False):
  """Create an OMS API client and start the requested authentication flow.

  Args:
    authentication: Name of the ``OMSAPI`` authentication method to call.
    verbose: Whether the OMS client should print request details.

  Returns:
    An authenticated OMS API client.
  """
  omsapi =  OMSAPI("https://cmsoms.cern.ch/agg/api", "v1", cert_verify=False, verbose=verbose)
  getattr(omsapi, authentication)()
  return omsapi

def fetch_data(datatype, dataid, omsapi):
  """Fetch one OMS record, retrying unsuccessful responses up to five times.

  Args:
    datatype: OMS resource name, such as ``'runs'`` or ``'lumisections'``.
    dataid: Resource identifier (or compound identifier for a lumisection).
    omsapi: Authenticated ``OMSAPI`` client.

  Returns:
    The decoded JSON response when successful, or an empty mapping after
    unsuccessful retries.
  """
  query = omsapi.query('/'.join([datatype, str(dataid)]))
  i=0
  response = query.data()
  while i<5 and not response.ok:
    response = query.data()
    i=i+1
  return response.json() if response.ok else {}
