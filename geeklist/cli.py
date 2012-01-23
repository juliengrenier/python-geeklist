# -*- coding: utf-8 -*-
import cmd
import json

from api import (BaseGeeklistApi,
                 GeekListUserApi,
                 GeekListOauthApi,
                 GeeklistProblem)

try:
    from access import consumer_info
except:
    consumer_info = {
        'key':'YOUR_CONSUMER_KEY',
        'secret': 'YOUR_CONSUMER_SECRET'
    }


class GeekCli(cmd.Cmd):
    prompt = 'geek>'

    def do_whoami(self, line):
        """
            whoami
            Print the user information about the current authenticate user
        """
        self.type = 'info'
        self.result = self.api.user_info()

    def do_whois(self, name):
        """
            whois name
            Print the user information about user named [name]
        """

        self.type = 'info'
        self.result = self.api.user_info(username=name)

    def __list_user_activities(self, line):
        line_tokens = line.split()
        self.name = line_tokens[0] if line_tokens else None
        self.filter_type = line_tokens[1] if line_tokens and \
                                             len(line_tokens) > 1 else None
        self.result = self.api.list_user_activities(
            username=self.name,
            filter_type=self.filter_type)
        self.count = len(self.result)

    def __autocomplete(self,list,text):
        if not text:
            completions = list
        else:
            completions = [f for f in list if f.startswith(text)]

        return completions

    def complete_list(self, text, line, begidx, endidx):
        list_types = ['activities','cards','micros','followers','following']
        return self.__autocomplete(list=list_types,text=text)

    def do_list(self, line):
        """
            list [activities\cards|micros|followers|following] [name]
        """
        line_tokens = line.split()
        self.type = line_tokens[0]
        if self.type == 'activities':
            return self.__list_user_activities(line.replace('activities', ''))
        self.name = line_tokens[1] if len(line_tokens) > 1 else None
        self.page = 1

        list_function = {
            'cards': self.api.list_cards,
            'micros': self.api.list_micros,
            'followers': self.api.list_followers,
            'following': self.api.list_following,
            }

        result = list_function[self.type](self.name)
        self.count = result['total_%s' % self.type]
        self.result = result[self.type]

    def do_fetch(self,line):
        fetch_functions = {
            'card':self.api.card,
            'cards':self.api.card,
            'micro':self.api.micro,
            'micros':self.api.micro
        }
        line_tokens = line.split(' ')
        if len(line_tokens) == 2:
            type = line_tokens[0]
            arg = line_tokens[1]

            if type not in ['card', 'micro']:
                self.result = "valid fetch objects are card and micro"
                return
        else:
            type = self.type
            arg = line_tokens[0]

        id = None
        if arg == 'last':
            id = self.result[-1]['id']
        elif arg == 'first':
            id = self.result[0]['id']

        if not id:
            try:
                index = int(arg)
                id = self.result[index]['id']
            except ValueError:
                id = arg

        function = fetch_functions[type]
        self.result = function(id)

    def do_show(self, attr):
        self.skip_print = True
        if attr == 'count':
            print self.count
            return
        if type(self.result) == dict:
            print self.result[attr]
        else:
            print [item[attr] for item in self.result]

    def do_get(self, index):
        """

        """
        if index == 'last':
            index = -1
        if index == 'first':
            index = 0
        try:
            self.result = self.result[int(index)]
        except IndexError:
            self.result = "there is only %s elements in the array" % \
                          len(self.result)
            return

    def do_authenticate(self, line):
        """
            This will authenticate you
        """
        self.oauth_api = GeekListOauthApi(consumer_info=consumer_info)
        request_token = self.oauth_api.request_token(type='oob')
        import webbrowser
        oauth_token = request_token['oauth_token']
        webbrowser.open(self.authorize_url + '?oauth_token=%s' % oauth_token)
        self.result = request_token
        print 'Once you got the verifier code from geekli.st. ' \
              'Call verify [code]'

    def do_verify(self, line):
        """
          verify [code]
          This will fetch an access code after you authenticated on geekli.st.
          You need to provide the verifier code shown on their website
        """
        self.result = self.oauth_api.access_token(self.result, line)
        access_token = self.result
        json_file = open(self.access_token_file_name, mode='w')
        json.dump(access_token,json_file)
        json_file.close()
        self.api = GeekListUserApi(
            consumer_info=consumer_info,
            token=access_token)

    def complete_create(self, text, line, begidx, endidx):
        return self.__autocomplete(list=['card', 'micro'],text=text)
    complete_h5 = complete_create
    complete_reply = complete_create

    def do_create(self, line):
        line_tokens = line.split(' ')
        type = line_tokens[0]
        text = ' '.join(line_tokens[1:])
        if type not in ['card', 'micro']:
            print "valid creation object are card and micro"
        if type == 'card':
            self.result = self.api.create_card(headline=text)
        elif type == 'micro':
            self.result = self.api.create_micro(status=text)
        self.type = type

    def do_h5(self, line):
        line_tokens = line.split(' ')
        type = line_tokens[0]
        object_id = line_tokens[1]
        if type not in ['card', 'micro']:
            self.result = "only card and micro can be highfived"

        if type == 'card':
            self.result = self.api.high_five_card(object_id)

        elif type == 'micro':
            self.result = self.api.high_five_micro(object_id)

    def do_reply(self, line):
        line_tokens = line.split(' ')
        type = line_tokens[0]
        object_id = line_tokens[1]
        text = line_tokens[2:]
        if type not in ['card', 'micro']:
            self.result = "valid reply objects are card and micro"
            return

        if type == 'card':
            self.result = api.reply_to_card(card_id=object_id, status=text)
        elif type == 'micro':
            self.result = api.reply_to_micro(micro_id=object_id, status=text)
        self.type = type

    def do_set_url(self, url):
        BaseGeeklistApi.BASE_URL = url
        self.result = "url is now %s" % BaseGeeklistApi.BASE_URL

    def do_next(self, count):
        if self.type not in ['followers',
                             'following',
                             'cards',
                             'micros',
                             'activities',
                             'stream']:
            self.result = "You must call list before calling next"
            return
        if count:
            count = count
        else:
            count = 10
        self.page += 1

        if self.type == 'activities':
            self.result = self.api.list_user_activities(
                username=self.name,
                filter_type=self.filter_type,
                page=self.page,
                count=count)
            return
        elif self.type == 'stream':
            self.result = self.api.list_all_activity(
                filter_type=self.filter_type,
                page=self.page,
                count=count)
            return

        list_functions = {
            'cards': self.api.list_cards,
            'micros': self.api.list_micros,
            'followers': self.api.list_followers,
            'following': self.api.list_following,
            }

        function = list_functions[self.type]
        result = function(self.name, page=self.page, count=count)
        self.count = result['total_%s' % self.type]
        self.result = result[self.type]

    def do_follow(self, name):
        """
            Follow [name]
            Will now follow [name] on geeklist
        """
        user = self.api.user_info(username=name)
        self.result = self.api.follow(user_id=user['id'])

    def do_unfollow(self, name):
        """
            Unfollow [name]
            Will unfollow [name] on geeklist
        """
        user = self.api.user_info(username=name)
        self.result = self.api.unfollow(user_id=user['id'])

    def do_stream(self, line):
        line_tokens = line.split(' ')
        filter_type = line_tokens[0] if line_tokens else None
        self.type = 'stream'
        self.name = None
        self.page = 1
        self.result = self.api.list_all_activity(filter_type=filter_type)
        self.count = len(self.result)

    def do_quit(self, *args):
        self.skip_print = True
        return True

    do_exit = do_quit

    def do_EOF(self, line):
        """Exit"""
        self.skip_print = True
        return True

    def postcmd(self, stop, line):
        if getattr(self, 'skip_print', False):
            self.skip_print = False
        elif not line.startswith('help'):
            if getattr(self, 'result', None):
                print json.dumps(self.result, indent=4)
        return cmd.Cmd.postcmd(self, stop, line)

    def onecmd(self, s):
        try:
            return cmd.Cmd.onecmd(self, s)
        except GeeklistProblem as problem:
            print problem.response

    def preloop(self):
        if not api:
            return self.do_authenticate('')
        return cmd.Cmd.preloop(self)


if __name__ == '__main__':
    BaseGeeklistApi.BASE_URL = 'http://sandbox-api.geekli.st/v1'
    authorize_url = 'http://sandbox.geekli.st/oauth/authorize'
    access_token_file_name = 'access.token.json'
    try:
        access_token_file = open(access_token_file_name,mode='r')
        access_token = json.load(access_token_file)
        api = GeekListUserApi(consumer_info=consumer_info, token=access_token)
    except:
        api = None

    cli = GeekCli()
    cli.api = api
    cli.access_token_file_name = access_token_file_name
    cli.authorize_url = authorize_url
    cli.cmdloop()
