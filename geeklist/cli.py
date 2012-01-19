# -*- coding: utf-8 -*-
import cmd
import json

from api import BaseGeeklistApi, GeekListUserApi, GeekListOauthApi, GeeklistProblem

from access import consumer_info, access_token

BaseGeeklistApi.BASE_URL = 'http://sandbox-api.geekli.st/v1'
api = GeekListUserApi(consumer_info=consumer_info, token=access_token)


class GeekCli(cmd.Cmd):
    prompt = 'geek>'

    def onecmd(self, s):
        try:
            return cmd.Cmd.onecmd(self, s)
        except GeeklistProblem as problem:
            print problem.response


    def do_whoami(self, line):
        """
            whoami
            Print the user information about the current authenticate user
        """
        self.type = 'info'
        self.result = api.user_info()

    def do_whois(self, name):
        """
            whois name
            Print the user information about user named [name]
        """

        self.type = 'info'
        self.result = api.user_info(username=name)

    def __list_user_activities(self, line):
        line_tokens = line.split()
        self.name = line_tokens[0] if line_tokens else None
        self.filter_type = line_tokens[1] if line_tokens and \
                                             len(line_tokens) > 1 else None
        self.result = api.list_user_activities(
            username=self.name,
            filter_type=self.filter_type)
        self.count = len(self.result)


    def __autocomplete(self,list,text):
        if not text:
            completions = list
        else:
            completions = [ f for f in list if f.startswith(text)]

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
            'cards': api.cards,
            'micros': api.micros,
            'followers': api.list_followers,
            'following': api.list_following,
            }

        result = list_function[self.type](self.name)
        self.count = result['total_%s' % self.type]
        self.result = result[self.type]

    def do_fetch(self,line):
        fetch_functions = {
            'card':api.card,
            'cards':api.card,
            'micro':api.micro,
            'micros':api.micro
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
        self.oauth_api = GeekListOauthApi(consumer_info=consumer_info)
        request_token = self.oauth_api.request_token(type='oob')
        import webbrowser
        webbrowser.open('http://sandbox.geekli.st/oauth/authorize?oauth_token=%s' % request_token['oauth_token'])

        self.result = request_token

    def do_verify(self, line):
        self.result = self.oauth_api.access_token(self.result, line)


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
            self.result = api.create_card(headline=text)
        elif type == 'micro':
            self.result = api.create_micro(status=text)
        self.type = type

    def do_h5(self, line):
        line_tokens = line.split(' ')
        type = line_tokens[0]
        object_id = line_tokens[1]
        if type not in ['card', 'micro']:
            self.result = "only card and micro can be highfived"

        if type == 'card':
            self.result = api.high_five_card(object_id)

        elif type == 'micro':
            self.result = api.high_five_micro(object_id)

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
            self.result = api.list_user_activities(
                username=self.name,
                filter_type=self.filter_type,
                page=self.page,
                count=count)
            return
        elif self.type == 'stream':
            self.result = api.list_all_activity(
                filter_type=self.filter_type,
                page=self.page,
                count=count)
            return

        list_functions = {
            'cards': api.cards,
            'micros': api.micros,
            'followers': api.list_followers,
            'following': api.list_following,
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
        user = api.user_info(username=name)
        self.result = api.follow(user_id=user['id'])

    def do_unfollow(self, name):
        """
            Unfollow [name]
            Will unfollow [name] on geeklist
        """
        user = api.user_info(username=name)
        self.result = api.unfollow(user_id=user['id'])

    def do_stream(self, line):
        line_tokens = line.split(' ')
        filter_type = line_tokens[0] if line_tokens else None
        self.type = 'stream'
        self.name = None
        self.page = 1
        self.result = api.list_all_activity(filter_type=filter_type)
        self.count = len(self.result)

    def do_quit(self, *args):
        self.skip_print = True
        return True

    do_exit=do_quit

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


if __name__ == '__main__':
    cli = GeekCli()
    cli.cmdloop()
