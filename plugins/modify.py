'''
'''
import pprint as pp
import calendar

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError

from rtmbot.core import Plugin
import utils.utils as utils
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
                self.outputs.append([data['channel'], response])

            elif commands[1].startswith('list:'): # Queries
                commands = commands[1:]
                for c in commands:
                    action_type, action, sliced = self.parse_command(c)
                    sliced = ' '.join(sliced)
                    try:
                        func = getattr(u, COMMAND_DICTIONARY[action_type][action])
                        task_listing = func(sliced)
                    except KeyError as e:
                        response = f"KeyError = {e}\n"
                    if action == 'details':
                        print(True)
                        attachment = self.format_task_details(task_listing, u)
                        print(attachment)
                        self.slack_client.api_call(
                            "chat.postMessage",
                            channel = data['channel'],
                            attachments = attachment
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


    def todo_formatting(self, todos):
        todo_dict = {}
        for t,v in todos.items():
            try:
                todo_dict[int(t)] = v
            except ValueError:
                pass
        todo_text = ''
        for todo, value in sorted(todo_dict.items()):
            title = value['todo']
            if value['done']:
                status = 'Complete'
                todo_text += f':ballot_box_with_check:  {todo}.  *{title}*\n\n'
            else:
                status = 'Open'
                todo_text += f':black_square_button:  {todo}.  *{title}*\n\n'
        return todo_text

    def comment_formatting(self, comments):
        comment_dict = {}
        for com in comments:
            for c,v in com.items():
                try:
                    comment_dict[int(c)] = v
                except ValueError:
                    pass
        comment_text = ''
        print(comment_dict)
        for comment, value in sorted(comment_dict.items()):
            title = value['comment']
            author = value['user']
            date_string = utils.format_datestring(value['datetime'])
            comment_text += f'{title}\n      - *{author}*   {date_string}\n'
        return comment_text

    def priority_formatting(self, task):
        priority = task['priorities'][str(task['priority'])]
        title = 'Priority'
        if task['time']['deadline'] is not None:
            date_string = utils.format_datestring(task['time']['deadline'])
            values += f' - Due:{date_string}'
        values = f'{priority}'
        return title, values

    def format_task_details(self, task, u):
        urgency_title, urgency_values = self.priority_formatting(task)
        attachment = [{
            'fallback': task['title'] + ' - ' + task['description'],
            'color': '#36a64f',
            'title': task['id'] + ' - ' + task['title'],
            'text': '  ' + task['description'],
            'mrkdwn_in': ['fields'],
            'fields': [
                {
                    'title': 'Stage',
                    'value': u.stage_name(task['workflow'], task['stage']),
                    'short' : True
                },
                {
                    'title': urgency_title,
                    'value': urgency_values,
                    'short' : True
                },
                {
                    'title': 'Assigned to',
                    'value': u.full_name(task['contributors']['assignee']),
                    'short' : False
                },
                {
                    'title': 'Todos',
                    'value': self.todo_formatting(task['todos']),
                    'short': False
                },
                {
                    'title': 'Comments',
                    'value': self.comment_formatting(task['comments']),
                    'short': False
                }
            ]
        }]
        return attachment

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
            if action_type == 'assign':
                response = f"    *{action_type}* : {sliced}\n"
            else:
                response = f"    *{action}* : {sliced}\n"
        except KeyError as e:
            response = f"KeyError = {e}\n"
        return response
