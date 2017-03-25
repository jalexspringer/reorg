from datetime import datetime

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError

from sec.sec import *
from libs.defaults import *


class Task:
    def __init__(self,
                 org,
                 title,
                 description,
                 user,
                 team=None,
                 is_parent=True,
                 workflow=None,
                 priorities=None,
                 assignee=None,
                 new_channel=False,
                 links=None,
                 template=None,
                 task_dictionary=None ):

        self.org = org
        self.user = user
        self.team = team
        if new_channel:
            channel = self.create_channel()
        else:
            channel = None

        if template is None:
            self.task_dictionary = {
                'title' : title,
                'description' : description,
                'endGoal': None,
                'isParent' : is_parent,
                'workflow' : workflow,
                'stage' : 0,
                'priorities' : priorities,
                'priority' : 0,
                'team' : team,
                'contributors' : {
                    # TODO Auto-populate reporter
                    'reporter' : user,
                    'assignee' : assignee,
                    'additional': None
                    },
                'channel' : None,
                'channelArchive': None,
                'tags' : [None],
                'subs' : None,
                'parent' : None,
                'time': {
                    'reported': r.expr(datetime.now(r.make_timezone('-05:00'))),
                    'resolved': (None, None),
                    'worklogs': {'U4LCZU3QD': 0},
                    'deadline': None,
                    },
                'history' : [],
                'comments' : [
                    # Tuple - (date, comment, user)
                    ],
                'links': links,
            }
        else:
            self.task_dictionary = template

    def replace_nones(self, c):
        user = r.db(self.org).table('users').get(self.task_dictionary['contributors']['reporter']).run(c)
        if self.team is None:
            self.task_dictionary['team'] = user['teams'][0][0]
        team = r.db(self.org).table('teams').get(self.task_dictionary['team']).run(c)
        if self.task_dictionary['workflow'] is None:
            self.task_dictionary['workflow'] = team['defaultWorkflow']
        if self.task_dictionary['priorities'] is None:
            self.task_dictionary['priorities'] = team['priorities']
        if self.task_dictionary['channel'] is None:
            self.task_dictionary['channel'] = team['teamChannel']

    def create_id(self, team, c):
        table = r.db(self.org).table(TEAMS_TABLE)
        table.get(team).update({
            'taskCount': r.row['taskCount']+1
        }).run(c)
        temp = table.get(team).run(c)['taskCount']
        task_num = str(temp)
        if len(task_num) < 3:
            task_num = '00' + task_num
        task_id = f'{team}-{task_num}'
        return task_id

    def commit(self):
        c = r.connect(DB_HOST, PORT)
        table = r.db(self.org).table(TASKS_TABLE)
        self.replace_nones(c)
        self.task_id = self.create_id(self.task_dictionary['team'], c)
        self.task_dictionary['id'] = self.task_id
        table.insert(self.task_dictionary).run(c)
        print(self.task_dictionary['id'], 'Committed.')

'''
def resolve(self, stage):
    self.task_dictionary['time']['resolved'] = (self.user, datetime.now())
    self.task_dictionary['stage'] = stage
    # TODO Workflow state change

def assign(self, ):
    ...

def next_stage(self, ):
    ...

def change_priority(self, ):
    ...

def add_subtask(self, ):
    ...

def add_contributor(self, ):
    ...

def log_time(self, ):
    ...

def start_clock(self, ):
    ...

def stop_clock(self, ):
    ...

def create_channel(self, ):
    ...

def archive_channel(self, ):
    ...

def comment(self, ):
    ...

def attach_file(self, ):
    ...

def add_tag(self, ):
    ...

def link_tasks(self, ):
    ...
'''
