import http.cookiejar as cookielib
import requests
import os, sys

def fetch_data(url, cookie):
  ''' fetch data from an OMS url using a pre-generated cookie
  '''
  req = requests.get(url, verify=True, cookies=cookie, allow_redirects=False)
  if not req.ok: return {}
  jsn = req.json()
  if not 'data' in jsn.keys(): return {}
  return jsn

def get_cookie(url):
  '''generate a cookie for the OMS website
  '''
  print('[INFO] generating cookie for', url)
  cookiepath = './.cookiefile_OMSfetch.txt'
  cmd = 'auth-get-sso-cookie --url "{}" -o {}'.format(url, cookiepath)
  ret = os.system(cmd)
  cookie = cookielib.MozillaCookieJar(cookiepath)
  cookie.load()
  os.remove(cookiepath)
  return cookie