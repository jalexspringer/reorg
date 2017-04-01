'''
'''
import pprint as pp

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError

from rtmbot.core import Plugin
from libs.users import AdminUser, ReOrgUser
from libs.task import NewTask
from libs.slack_response import SlackResponder
from sec.sec import *
from libs.defaults import *

class UserPlugin(Plugin):

    # sr.bot_id = r.db(CLIENT_DB).table(CLIENT_TABLE).get(self.org).run(self.c)['platform']['reorgBotID']
    def process_message(self, data):

        conn = r.connect(DB_HOST, PORT)
        if data['text'].startswith('$'):
            org = r.db(CLIENT_DB).table(CLIENT_TABLE).filter({'platform':{'slackTeamID': data['source_team']}}).pluck('id').max().run(conn)['id']

            sr = SlackResponder()
            # Establish permissions
            if sr.is_admin(org, data['user'], conn):
                u = AdminUser(org, data['user'])
            else:
                u = ReOrgUser(org, data['user'])


            # Parse commands
            commands = data['text'].split('$')
            if commands[1].startswith('create'): # New task creation
                new_task_info = {}
                for c in commands[2:]:
                    field, sliced = sr.parse_create_command(c)
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
                    # TODO Create secondary dictionary only including correct kwargs.
                    response = "Womp. No luck - please consult documentation for valid arguments to create.\n"
                t.commit()
                response = f'New task {t.task_id} created.\n'
                self.outputs.append([data['channel'], response])

            elif commands[1].startswith('list:'): # Queries
                commands = commands[1:]
                for c in commands:
                    action_type, action, sliced = sr.parse_command(c)
                    sliced = ' '.join(sliced)
                    if action == 'details':
                        func = getattr(u, COMMAND_DICTIONARY[action_type][action])
                        task_listing = func(sliced)
                        attachment = sr.format_task_details(task_listing, u)
                        self.slack_client.api_call(
                            "chat.postMessage",
                            channel = data['channel'],
                            attachments = attachment
                        )
                    elif action == 'tasks' or action == 'todos':
                        func = getattr(u, COMMAND_DICTIONARY[action_type][action])
                        listing = func()
                        attachment = sr.format_tasks(listing, u)
                        self.slack_client.api_call(
                            "chat.postMessage",
                            channel = data['channel'],
                            text = 'Your tasks:',
                            attachments=attachment
                        )

                    else:
                        func = getattr(u, COMMAND_DICTIONARY[action_type][action])
                        listing = func()
                        self.slack_client.api_call(
                            "chat.postMessage",
                            channel = data['channel'],
                            text = listing
                        )
            else: #Existing task modifications
                task = commands[1].strip()
                t = u.open_task(task)
                commands = commands[2:]
                response = f'>>>Task {t.task_id} updated:\n'
                for c in commands:
                    # Admin commands
                    if c.startswith('admin:'):
                        if u.admin:
                            action_type, action, sliced = sr.parse_command(c)
                        else:
                            response += u.non_admin_response(c)

                    # Non-admin commands
                    else:
                        action_type, action, sliced = sr.parse_command(c)
                        if action_type in COMMAND_DICTIONARY:
                            if action in ['comment']:
                                sliced = ' '.join(sliced)
                            response += sr.call_func(t, action_type, action, sliced)

                        else:
                            response += f"Unknown action type {action_type}\n"
                t.commit()
                self.outputs.append([data['channel'], response])


