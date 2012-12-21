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
    page_count = 10
    gklist_objects = ['card', 'micro', 'link']
    listable_objects = ['followers', 'following', 'cards', 'micros', 'activities', 'links', 'stream', 'populars']

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

    def _list_user_activities(self, line):
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
        list_types = self.listable_objects
        return self.__autocomplete(list=list_types,text=text)

    def _call_list_function(self):
        function = getattr(self.api,'list_'+self.type)
        result = function(self.name,self.page,self.page_count)
        if self.type == 'populars':
            self.result = result['links']
            self.count = len(self.result)
        else:
            self.result = result[self.type]
            self.count = result['total_%s' % self.type]

    def do_list(self, line):
        """
            list [activities|cards|micros|followers|following|populars|links] [name]
            Return the list of objects for a given [name]. If no name is
            provided Then it will return the list for the current authenticated user.

            After this command. You can use :
                next : to fetch the next page of result.
                show [attr] : to list an attribute.
                get [index] : to retrieve a specific object.
        """
        line_tokens = line.split()
        self.type = line_tokens[0]
        if self.type == 'activities':
            return self._list_user_activities(line.replace('activities', ''))
        self.name = line_tokens[1] if len(line_tokens) > 1 else None
        self.page = 1
        self._call_list_function()

    def do_fetch(self,line):
        """
            fetch [card|micro] id

            This will fetch a card or micro information given its id.

        """
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

            if type not in self.gklist_objects:
                self.result = "valid fetch objects are card and micro"
                return
        else:
            type = self.type
            arg = line_tokens[0]

        id = arg

        function = fetch_functions[type]
        self.result = function(id)

    def do_show(self, attr):
        """
            show attribute
            If attribute == 'count' Then show the total of object created
            Else This will print the attribute for each object return from the last command
        """
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
            get index
            Retrieve the object at position [index].
            Note: first and last are valid arguments
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
        return self.__autocomplete(list=self.gklist_objects,text=text)
    complete_h5 = complete_create
    complete_reply = complete_create

    def do_create(self, line):
        """
            create {0} text...
            This will create a card or a micro. The rest of the line will be the arguments of created object
            examples:
                create card headline
                create micro status
                create link url|title|description|communities|category #only url and title are required, communities are comma-separated
        """.format(self.gklist_objects)
        line_tokens = line.split(' ')
        type = line_tokens[0]
        text = ' '.join(line_tokens[1:])
        if type not in self.gklist_objects:
            print "valid creation object are card and micro"

        if type == 'card':
            self.result = self.api.create_card(headline=text)
        elif type == 'micro':
            self.result = self.api.create_micro(status=text)
        elif type == 'link':
            self.result = self.api.create_link(*text.split("|"))
        self.type = type

    def do_h5(self, line):
        """
            h5 [card|micro] [id]
            This will send an h5 for the object
        """
        line_tokens = line.split(' ')
        type = line_tokens[0]
        object_id = line_tokens[1]
        if type not in self.gklist_objects:
            self.result = "only card and micro can be highfived"

        if type == 'card':
            self.result = self.api.high_five_card(object_id)

        elif type == 'micro':
            self.result = self.api.high_five_micro(object_id)

    def do_reply(self, line):
        """
            reply [card|micro] id text...
            Create a micro in reply to a card or micro with the rest of the
            line as the text
        """
        line_tokens = line.split(' ')
        type = line_tokens[0]
        object_id = line_tokens[1]
        text = line_tokens[2:]
        if type not in self.gklist_objects:
            self.result = "valid reply objects are card and micro"
            return

        if type == 'card':
            self.result = api.reply_to_card(card_id=object_id, status=text)
        elif type == 'micro':
            self.result = api.reply_to_micro(micro_id=object_id, status=text)
        self.type = type

    def do_set_url(self, url):
        """
            set_url url
            Change the base url
        """
        BaseGeeklistApi.BASE_URL = url
        self.result = "url is now %s" % BaseGeeklistApi.BASE_URL

    def do_next(self, ignore):
        """
            next
            This will fetch the next page of elements
        """
        if self.type not in self.listable_objects:
            self.result = "You must call list before calling next"
            return

        self.page += 1

        if self.type == 'activities':
            self.result = self.api.list_user_activities(
                username=self.name,
                filter_type=self.filter_type,
                page=self.page,
                count=self.page_count)
            return
        elif self.type == 'stream':
            self.result = self.api.list_all_activity(
                filter_type=self.filter_type,
                page=self.page,
                count=self.page_count)
            return

        self._call_list_function()

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
        """
            stream [filter]
            Return the activity stream of geekli.st filtered by [filter]
        """
        line_tokens = line.split(' ')
        self.filter_type = line_tokens[0] if line_tokens else None
        self.type = 'stream'
        self.name = None
        self.page = 1
        self.result = self.api.list_all_activity(filter_type=self.filter_type,
            page=self.page,
            count=self.page_count)
        self.count = len(self.result)

    def do_page_count(self,count):
        """
            page_count number
            Set the number of results per page
        """
        self.page_count = count

    def do_quit(self, *args):
        self.skip_print = True
        return True

    do_exit = do_quit

    def do_EOF(self, line):
        """Exit"""
        self.skip_print = True
        return True

    def postcmd(self, stop, line):
        """
            Executed after each command. This will usually print
            the result of the command unless the skip_print variable have been set to True

        """
        if getattr(self, 'skip_print', False):
            self.skip_print = False
        elif not line.startswith('help'):
            if getattr(self, 'result', None):
                print json.dumps(self.result, indent=4)
        return cmd.Cmd.postcmd(self, stop, line)

    def onecmd(self, s):
        """
            Wrap each command to avoid quitting the loop because of an API error.
        """
        try:
            return cmd.Cmd.onecmd(self, s)
        except GeeklistProblem as problem:
            print problem.response

    def preloop(self):
        """
            Make sure we have access to geekli.st.
            If not this will call authenticate for us.
        """
        if not self.api:
            return self.do_authenticate('')
        return cmd.Cmd.preloop(self)


if __name__ == '__main__':
    authorize_url = 'http://geekli.st/oauth/authorize'
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
