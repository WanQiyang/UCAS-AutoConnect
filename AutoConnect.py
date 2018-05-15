#!/usr/bin/env python
#_*_coding:utf-8_*_

import logging
import socket
import threading
import urllib2
import urlparse
from logging.handlers import TimedRotatingFileHandler
import csv
import json
import random
import sys

global timer
global logger
global log_file_handler
global users
global ip

AUTH_IP = '0.0.0.0'

def init_logger():
  global logger
  global log_file_handler
  fmt = '%(asctime)s %(levelname)s - %(message)s'
  formatter = logging.Formatter(fmt)
  log_file_handler = TimedRotatingFileHandler(filename='AutoConnect.log', when="D", interval=1, backupCount=3)
  log_file_handler.setFormatter(formatter)
  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger()
  logger.addHandler(log_file_handler)

def destroy_logger():
  global logger
  global log_file_handler
  logger.removeHandler(log_file_handler)

def get_global_ip():
  global ip
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect((AUTH_IP, 80))
  ip = s.getsockname()[0]
  s.close()

def load_users():
  global logger
  global users
  users = []
  with open('Users', 'r') as f:
    csv_file = csv.reader(f)
    for user in csv_file:
      users.append(user)
  logger.info('%d user(s) loaded.' % len(users))

def set_encoding():
  reload(sys)
  sys.setdefaultencoding('utf-8')

def init():
  global logger
  global ip
  init_logger()
  logger.info('AutoConnect service start.')
  load_users()
  get_global_ip()
  logger.info('Global IP: %s.' % ip)

def destroy():
  global logger
  logger.info('AutoConnect service stop.')
  destroy_logger()

def connect(query):
  global logger
  global users
  global ip
  random.shuffle(users)
  for user in users:
    headers = {'Content-Type': 'application/json'}
    data={'password' : user[1], 'queryString' : query, 'service' : '', 'userAgent' : 'PC', 'userId' : user[0], 'userip' : ip}
    data=bytes(json.dumps(data))
    request = urllib2.Request(url='http://' + AUTH_IP + '/eportal/inferface/authAPI/login', headers=headers, data=data)
    response = json.loads(urllib2.urlopen(request).read())
    if not 'result' in response:
      logger.error('Failed to connect with user "%s". Network error.' % user[0])
    elif response['result'] == 'fail':
      logger.error('Failed to connect with user "%s". %s' % (user[0], response['message']))
    elif response['result'] == 'success':
      logger.info('Connected with user "%s".' % user[0])
      return
    else:
      logger.error('Failed to connect with user "%s". Response: %s.' % (user[0], response['result']))

  logger.error('No user available.')
  destroy()
  sys.exit()

def check_connection():
  try:
    global logger
    logger.info('Check connection.')
    page_entry = urllib2.urlopen('http://' + AUTH_IP +'/eportal/gologout.jsp')
    parsed_url = urlparse.urlparse(page_entry.geturl())
    if parsed_url.path.find('success') == -1:
      logger.info('Disconnected. Attempt to connect.')
      connect(parsed_url.query)
    else:
      logger.info('Connected. Do nothing.')

    global timer
    timer = threading.Timer(60, check_connection)
    timer.start()

  except Exception as e:
    logger.error(e)
    destroy()

if __name__ == '__main__':
  set_encoding()
  init()
  check_connection()
