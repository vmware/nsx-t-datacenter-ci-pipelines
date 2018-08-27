#!/usr/bin/env python

# nsx-t-gen
#



from __future__ import absolute_import, division, print_function

__author__ = 'Sabha Parameswaran'

import sys
import yaml
import json
import requests
import time
from requests.auth import HTTPDigestAuth
from pprint import pprint

try:
  # Python 3
  from urllib.parse import urlparse
except ImportError:
  # Python 2
  from urlparse import urlparse

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

class auth(requests.auth.AuthBase):

  def __init__(self, context):
    self.context = context

  def __call__(self, request):
    username = self.context.get('admin_user')
    password = self.context.get('admin_passwd')
    return requests.auth.HTTPBasicAuth(username, password)(request) 

def get_context():
  if get_context.context is not None:
    return get_context.context
  else:
    raise Error('config not loaded!!')

get_context.context = None

def set_context(context):
  get_context.context = context

def get(url, stream=False, check=True):
  context = get_context()
  url = context.get('url') + url
  headers = { 'Accept': 'application/json,text/html,application/xhtml+xml,application/xml' }
  
  response = requests.get(url, auth=auth(context), verify=False, headers=headers, stream=stream)
  check_response(response, check=check)
  return response

def put(url, payload, check=True):
  try:
    context = get_context()
    url = context.get('url') + url
    response = requests.put(url, auth=auth(context), verify=False, json=payload)
    check_response(response, check=check)
    return response
  except:
    # Squelch Python error during put operations:
    # File "/usr/local/lib/python2.7/site-packages/requests/packages/urllib3/connectionpool.py", line 314, in _raise_timeout
    #     if 'timed out' in str(err) or 'did not complete (read)' in str(err):  # Python 2.6
    # TypeError: __str__ returned non-string (type SysCallError)
    #print('Error during put')
    return ''

def post(url, payload, check=True):
  context = get_context()
  url = context.get('url') + url
  response = requests.post(url, auth=auth(context), verify=False, json=payload)
  check_response(response, check=check)
  return response

def delete(url, check=True):
  context = get_context()
  url = context.get('url') + url
  response = requests.delete(url, auth=auth(context), verify=False)
  check_response(response, check=check)
  return response

def check_response(response, check=True):
  #pprint(vars(response))
  #print(response.content)
  if check and (response.status_code != requests.codes.ok and response.status_code > 400):
    
    print('-', response.status_code, response.request.url, file=sys.stderr)
    try:
      errors = response.json()["errors"]
      print('- '+('\n- '.join(json.dumps(errors, indent=4).splitlines())), file=sys.stderr)
    except:
      print(response.text, file=sys.stderr)
    sys.exit(1)
