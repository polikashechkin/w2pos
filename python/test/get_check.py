import os, sys, datetime, requests, pickle, json
python = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(python)

from domino.server import Server, GUID
from domino.cli  import print_comment, Console, print_header, print_warning

import json
import xml.etree.ElementTree as ET
from domino.core import log
from domino.application import Status
from domino.account import find_account_id


if __name__ == "__main__":
    c = Console(__file__)
    params= {}
    params['account_id'] = c.input('account_id')
    params['dept_uid'] =  c.input('dept_uid')
    params['fr_uid']= c.input('fr_uid')
    params['date'] = c.input('date')
    params['fr_smena'] = c.input('fr_smena')
    params['fr_number'] = c.input('fr_number')
    r = requests.get('https://dev.domino.ru/w2pos/active/python/get_check', params)
    print(r.url)
    print_header(r.status_code)
    print_warning(r.text)



