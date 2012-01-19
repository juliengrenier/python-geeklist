# -*- coding: utf-8 -*-
from geeklist.geeklist import BaseGeeklistApi, GeekListOauthApi, GeekListUserApi

from access import consumer_info#, access_token

BaseGeeklistApi.BASE_URL ='http://sandbox-api.geekli.st'
geeklist_oauth_api = oauth_api = GeekListOauthApi(consumer_info=consumer_info)
request_token = geeklist_oauth_api.request_token()
import webbrowser
webbrowser.open('http://sandbox.geekli.st/oauth/authorize?%s' % request_token['oauth_token'])

#read verifier
verifier = raw_input(prompt='Please enter verifier code')
new_access_token = geeklist_oauth_api.access_token(request_token=request_token, verifier=verifier)
BaseGeeklistApi.BASE_URL = 'http://sandbox-api.geekli.st/v1'
user_api = GeekListUserApi(consumer_info, new_access_token)
print user_api.user_info()
user_api.create_card(headline='First card created with the python wrapper API')

