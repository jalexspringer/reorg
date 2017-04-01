import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError
from sec.sec import *
import utils.utils as utils
from libs.defaults import *

class SlackResponder:

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

    def comment_formatting(self, comments, u):
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
            author = u.full_name(value['user'])
            date_string = utils.format_datestring(value['datetime'])
            comment_text += f'{title}\n      - *{author}* {date_string}\n'
        return comment_text

    def priority_formatting(self, task):
        priority = task['priorities'][str(task['priority'])]
        title = 'Priority'
        if task['time']['deadline'] is not None:
            date_string = utils.format_datestring(task['time']['deadline'])
            values += f' - Due:{date_string}'
        values = f'{priority}'
        return title, values

    def format_tasks(self, listing, u):
        attachment = []
        for i in listing:
            print(i)
            attachment.append({
                'fallback': i['title'],
                'color': ATT_COLOR,
                'title': ':black_square_button:  '  + i['id'] + ' - ' + i['title'],
            })
        return attachment

    def format_task_details(self, task, u):
        urgency_title, urgency_values = self.priority_formatting(task)
        attachment = [{
            'fallback': task['title'] + ' - ' + task['description'],
            'color': ATT_COLOR,
            'author_name': 'Task ' + task['id'],
            'title': task['title'],
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
                    'value': self.comment_formatting(task['comments'], u),
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
