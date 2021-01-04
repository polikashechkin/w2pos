import sys, os, json, sqlite3, arrow, datetime
from flask import Flask, request
#import xml.etree.cElementTree as ET
from domino.core import log
#from domino.application import Status
#from domino.databases import Databases
#from domino.account import find_account_id
from domino.application import Application
from domino.databases.oracle import Oracle
from domino.databases.postgres import Postgres

#from responses.get_check import get_check
#from domino.account import find_account
#from domino.page import Page
                                              
app = Flask(__name__)
application = Application(os.path.abspath(__file__), framework='MDL')

ORACLE = Oracle.Pool()
POSTGRES = Postgres.Pool()

#databases = Databases()

#def get_db_connection(account_id):
#    database = databases.get_database(account_id)
#    return database.connect()
      
import pages.start_page
@app.route('/pages/start_page')
@app.route('/pages/start_page.<fn>')
def _pages_start_page(fn=None):
    return application.response(request, pages.start_page.Page, fn)

import pages.checks 
@app.route('/pages/checks')
@app.route('/pages/checks.<fn>')
def _pages_checks(fn=None):
    return application.response(request, pages.checks.Page, fn, [ORACLE, POSTGRES])

import pages.check 
@app.route('/pages/check')
@app.route('/pages/check.<fn>')
def _pages_check(fn=None):
    return application.response(request, pages.check.Page, fn, [ORACLE, POSTGRES])
     

@app.route('/about', methods=['GET','POST'])
def about():
    return 'about'

import responses.get_check
@app.route('/get_check', methods=['GET','POST'])
def _responses_get_check(fn = None):
    return application.response(request, responses.get_check.Response, fn, [ORACLE, POSTGRES], log=True)

def navbar(page): 
    nav = page.navbar()
    nav.header(f'Возврат чеков', 'pages/start_page')
    nav.item('Чеки', 'pages/checks')
                                     
application['navbar'] = navbar          
