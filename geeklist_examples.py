# -*- coding: utf-8 -*-
from geeklist.api import BaseGeeklistApi, GeekListOauthApi, GeekListUserApi

from access import consumer_info #please access.py which contains consumer_info = { 'key': YOUR_KEY, 'secret': secret}

BaseGeeklistApi.BASE_URL ='http://sandbox-api.geekli.st/v1'
oauth_api = GeekListOauthApi(consumer_info=consumer_info)
request_token = oauth_api.request_token(type='oob')
import webbrowser
webbrowser.open('http://sandbox.geekli.st/oauth/authorize?oauth_token=%s' % request_token['oauth_token'])

#read verifier
verifier = raw_input('Please enter verifier code>')
oauth_access_token = oauth_api.access_token(request_token=request_token, verifier=verifier)
access_token = {
    'key':oauth_access_token['oauth_token'],
    'secret':oauth_access_token['oauth_token_secret']
}
user_api = GeekListUserApi(consumer_info, access_token)
print user_api.user_info()
user_api.create_card(headline='First card created with the python wrapper API')

