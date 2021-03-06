import oauth2 as oauth
import urllib
import json
import urlparse


class GeeklistProblem(Exception):
    def __init__(self):
        super(GeeklistProblem, self).__init__()

    @classmethod
    def create(cls, url, statuscode, response):
        hp = cls()
        hp.url = url
        hp.statuscode = statuscode
        hp.response = response
        return hp

    def __unicode__(self, *args, **kwargs):
        return u"Geeklist request to %s failed with status %s, response %s" % \
               (self.url, self.statuscode, self.response)

    def __str__(self):
        return str(unicode(self))


class BaseGeeklistApi(object):
    """A Geeklist API client."""

    BASE_URL = 'http://api.geekli.st/v1'
    FILTER_TYPES = ['card', 'micro', 'follow', 'highfive']

    def __init__(self, consumer_info, token):
        """
            consumer_info : Dictionary like this one:
                {
                    'key':YOUR_APP_KEY,
                    'secret':YOUR_APP_SECRET
                }
            token : If None you must get an request_token and an access token
                    before accessing other API methods.
                    This is a dictionary :
                    {
                        'oauth_token':TOKEN
                        'oauth_token_secret':TOKEN_SECRET
                    }
        """
        self.consumer = oauth.Consumer(
            key=consumer_info['key'],
            secret=consumer_info['secret']
        )
        if token:
            oauth_token = oauth.Token(
                token['oauth_token'],
                token['oauth_token_secret'])
        else:
            oauth_token = None
        self.client = oauth.Client(self.consumer, token=oauth_token)

    def _request(self, url, method='GET', body={}, decode=True):
        if url.startswith('/'):
            url = self._build_url(url)

        body_string = urllib.urlencode(body)

        (resp, content) = self.client.request(url,
            method, body=body_string)
        if resp.status == 200:
            if decode:
                json_response = json.loads(content)
                if json_response.get('status',None) == 'ok' and \
                   'data' in json_response:
                    return json_response['data']
                else:
                    return json_response
            else:
                return content

        statuscode = resp.status
        raise GeeklistProblem.create(
            url=url,
            statuscode=statuscode,
            response=content)

    def _build_url(self,path):
        return BaseGeeklistApi.BASE_URL + path


class GeekListOauthApi(BaseGeeklistApi):
    APP_TYPES = ['web', 'oob']

    def __init__(self, consumer_info):
        super(GeekListOauthApi, self).__init__(
            consumer_info=consumer_info,
            token=None)

    def request_token(self, type='web'):
        """
            Return a dictionary containing the request token key and request
            token secret
        """
        if type not in GeekListOauthApi.APP_TYPES:
            raise ValueError('type must in %s' % GeekListOauthApi.APP_TYPES)

        request_token_url = '/oauth/request_token'

        if type == 'oob':
            content = self._request(
                url='%s?oauth_callback=oob' % request_token_url,
                decode=False)
        else:
            content = self._request(url=request_token_url, decode=False)

        request_token = dict(urlparse.parse_qsl(content))
        return request_token

    def access_token(self, request_token, verifier):
        """
            request_token: a dictionary containing the request token key and
            the request token secret :
                {
                    'oauth_token': REQ_TOKEN_KEY,
                    'oauth_token_secret' : REQ_TOKEN_SECRET
                }
            verifier : The verifier return from Geeklist.
        """
        token = oauth.Token(request_token['oauth_token'],
            request_token['oauth_token_secret'])
        token.set_verifier(verifier)
        self.client = oauth.Client(self.consumer, token=token)
        access_token_url = '/oauth/access_token'

        content = self._request(url=access_token_url, decode=False)
        access_token = dict(urlparse.parse_qsl(content))
        return access_token


class GeekListUserApi(BaseGeeklistApi):
    def __init__(self, consumer_info, token):
        if not token:
            raise ValueError("A valid token must use to "
                             "access the geeklist user api")
        super(GeekListUserApi, self).__init__(
            consumer_info=consumer_info,
            token=token)

    def _build_list_url(self, list_type, username, page, count):
        if username:
            url = '/users/%s' % username
        else:
            url = '/user'

        url = '%s/%s' % (url, list_type)

        if page and count:
            url += '?page=%s&count=%s' % (page, count)
        elif page:
            url += '?page=%s' % page
        elif count:
            url += '?count=%s' % count

        return url

    def user_info(self, username=None, page=1, count=10):
        url = self._build_list_url(list_type='',
            username=username,
            page=page,
            count=count)
        return self._request(url=url)

    def _list_items(self, items='', username=None, page=1, count=10):
        url = self._build_list_url(list_type=items,
            username=username,
            page=page,
            count=count)
        return self._request(url=url)

    def list_cards(self, username=None, page=1, count=10):
        return self._list_items('cards', username=username,
                page=page,
                count=count)

    def list_micros(self, username=None, page=1, count=10):
        return self._list_items('micros', username=username,
                page=page,
                count=count)

    def list_followers(self, username, page=1, count=10):
        return self._list_items('followers', username=username,
                page=page,
                count=count)

    def list_following(self, username, page=1, count=10):
        return self._list_items('following', username=username,
                page=page,
                count=count)

    def list_links(self, username, page=1, count=10):
        return self._list_items('links', username=username,
                page=page,
                count=count)

    def list_populars(self, communities, page=1, count=10):
        url='/links?page={0}&count={1}'.format(page, count)
        if communities:
            url += "&communities="+communities
        return self._request(url=url)

    def card(self, id):
        url = '/cards/%s' % id
        return self._request(url=url)

    def create_card(self, headline):
        url = '/cards'
        return self._request(url=url,
            method='POST',
            body={'headline': headline})

    def micro(self, id):
        url = '/micros/%s' % id
        return self._request(url=url)

    def create_micro(self, status):
        url = '/micros'
        return self._request(url=url,
            method='POST',
            body={'status': status})

    def reply_to_micro(self, micro_id, status):
        url = '/micros'
        return self._request(url=url, method='POST', body={
            'status': status,
            'type': 'micro',
            'in-reply-to': micro_id
        })

    def reply_to_card(self, card_id, status):
        url = '/micros'
        return self._request(url=url, method='POST', body={
            'status': status,
            'type': 'card',
            'in-reply-to': card_id
        })

    def create_link(self, link_url, title, description=None, communities=None, category='My links'):
        url = '/links'
        body={
            'url': link_url,
            'title': title,
        }
        if description: body.update(description=description)
        if communities: body.update(communities=communities)
        if category: body.update(category=category)
        return self._request(url=url, method='POST', body=body)

    def follow(self, user_id):
        url = '/follow'
        return self._request(url=url, method='POST', body={
            'user': user_id,
            'action': 'follow'
        })

    def unfollow(self, user_id):
        url = '/follow'
        return self._request(url=url, method='POST', body={
            'user': user_id
        })

    def list_user_activities(self,
                             username=None,
                             filter_type=None,
                             page=1,
                             count=10):

        if filter_type and filter_type not in BaseGeeklistApi.FILTER_TYPES:
            raise ValueError("Wrong filter")

        url = self._build_list_url(list_type='activity',
            username=username,
            page=page,
            count=count)

        if filter_type:
            url += '&card=%s' % filter_type
        return self._request(url=url)

    def list_all_activity(self, filter_type, page=1, count=10):
        if filter_type and filter_type not in BaseGeeklistApi.FILTER_TYPES:
            raise ValueError("Wrong filter")

        url = '/activity?'
        if page and count:
            url += 'page=%s&count=%s' % (page, count)
        elif page:
            url += 'page=%s' % page
        elif count:
            url += 'count=%s' % count

        if filter_type:
            url += '&type=%s' % filter_type

        return self._request(url)

    def _high_five(self, item_type, item_id):
        url = '/highfive'
        return self._request(url, method='POST', body={
            'type': item_type,
            'gfk': item_id
        })

    def high_five_card(self, card_id):
        return self._high_five('card', card_id)

    def high_five_micro(self, micro_id):
        return self._high_five('micro', micro_id)
