'''
'''

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError

from rtmbot.core import Plugin
from libs.users import AdminUser, ReOrgUser
from libs.task import NewTask
from sec.sec import *
from libs.defaults import *

class UserPlugin(Plugin):

    # self.bot_id = r.db(CLIENT_DB).table(CLIENT_TABLE).get(self.org).run(self.c)['platform']['reorgBotID']
    def process_message(self, data):

        conn = r.connect(DB_HOST, PORT)
        if data['text'].startswith('$'):
            org = r.db(CLIENT_DB).table(CLIENT_TABLE).filter({'platform':{'slackTeamID': data['source_team']}}).pluck('id').max().run(conn)['id']

            # Establish permissions
            if self.is_admin(org, data['user'], conn):
                u = AdminUser(org, data['user'])
            else:
                u = ReOrgUser(org, data['user'])

            # Parse commands
            response = ''
            commands = data['text'].split('$')
            print(commands)
            if commands[1].startswith('create:'): # New task creation
                new_task_info = {}
                for c in commands[2:]:
                    field, sliced = self.parse_create_command(c)
                    new_task_info[field] = sliced
                    try:
                        del new_task_info['']
                    except KeyError:
                        pass
                    try:
                        del new_task_info[' ']
                    except KeyError:
                        pass
                try:
                    t = NewTask(org=org, user=data['user'], **new_task_info)
                except TypeError:
                    # TODO List field options - disregard incorrect ones as long as the right ones are there?
                    # TODO Create secondary dictionary only including correct kwargs.
                    response = "Womp. No luck - please consult documentation for valid arguments to create.\n"
                t.commit()
                response += f'New task {t.task_id} created.\n'
            else: #Existing task modifications
                task = commands[1].strip()
                t = u.open_task(task)
                commands = commands[2:]
                for c in commands:
                    # Admin commands
                    if c.startswith('admin:'):
                        if u.admin:
                            action_type, action, sliced = self.parse_command(c)
                        else:
                            response += u.non_admin_response(c)

                    # Non-admin commands
                    else:
                        action_type, action, sliced = self.parse_command(c)
                        if action_type in COMMAND_DICTIONARY:
                            if action in ['comment']:
                                sliced = ' '.join(sliced)
                            response += self.call_func(t, action_type, action, sliced)
                        else:
                            response += f"Unknown action type {action_type}\n"
                t.commit()
            self.outputs.append([data['channel'], response])

    def parse_command(self, c, join=False):
        cut = c.split(':')
        action_type = cut[0]
        sliced = cut[1].split(' ')
        action = sliced[0]
        sliced = sliced[1:]
        sliced = ' '.join(sliced)
        sliced = sliced.split(', ')
        print(action_type,action,sliced)
        return action_type, action, sliced

    def parse_create_command(self, c):
        print(c)
        cut = c.split(':')
        print(cut)
        field = cut[0]
        value = cut[1]
        print(field, value)
        return field, value

    def is_admin(self, org, user, conn):
        return r.db(org).table(USER_TABLE).get(user).run(conn)['admin']

    def call_func(self, t, action_type, action, sliced):
        try:
            func = getattr(t, COMMAND_DICTIONARY[action_type][action])
            func(sliced)
            response = f"Successfully added {action}:{sliced} to {t.task_id}\n"
        except KeyError as e:
            response = f"KeyError = {e}\n"
        return response
