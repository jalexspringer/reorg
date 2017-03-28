from datetime import datetime

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError

from sec.sec import *
from libs.defaults import *
from libs.workflow import Workflow

class Task:
    def __init__(self, org, task_id, user):
        self.org = org
        self.task_id = task_id
        self.user = user
        self.c = r.connect(DB_HOST, PORT)
        self.task = r.db(org).table(TASKS_TABLE).get(task_id)
        self.task_record = self.task.run(self.c)
        self.update_dictionary = {}
        self.stage = self.task_record['stage']
        flowlist = r.db(self.org).table('workflows').get(self.task_record['workflow']).run(self.c)
        self.flow = Workflow(flowlist['flowlist'], flowlist['id'])

    def modified_date_time(self):
        return {'lastModified': r.expr(datetime.now(r.make_timezone('-05:00'))),
        'modifiedBy': self.user}

    def backup(self):
        try:
            current_history = self.task_record['history']
        except KeyError:
            current_history = []
        to_archive = {i:self.task_record[i] for i in self.task_record if i!='history'}
        print(to_archive)
        current_history.insert(0, to_archive)
        print(current_history)
        if len(current_history) >= 10:
            current_history.pop()
        self.task.update({'history': current_history}).run(self.c)

    def commit(self, to_backup=False):
        try:
            if not self.update_dictionary['open']:
                self.update_dictionary.update({'time':
                                               {'resolved': [r.expr(datetime.now(r.make_timezone('-05:00'))),
                                                             self.user]
                                               }})
        except KeyError:
            pass
        if 'stage' in self.update_dictionary:
            self.flow.do(self.stage, self.task_id)
            to_backup = True
        if to_backup:
            self.backup()
        self.update_dictionary.update(self.modified_date_time())
        self.task.update(self.update_dictionary).run(self.c)
        self.task_record = self.task.run(self.c)
        self.update_dictionary = {}
        print('Updated record:\n', self.task_id)
        response = self.task_id, 'Committed.'
        return response

    def pending_changes(self):
        response = self.update_dictionary
        print(response)
        return response

    def assign_task(self, assignee):
        try:
            current = self.update_dictionary['contributors']
            current['assignee'] = assignee
        except KeyError:
            current = {'assignee': assignee}
        self.update_dictionary.update({'contributors': current})
        response = 'New assignee added to update queue.'
        return response

    def assign_todo(self, assignee, todo):
        try:
            current = self.task_record['todos'][str(todo)]
        except KeyError:
            response = 'No such todo!'
            return response
        self.update_dictionary.update({'todos': {str(todo): {'assignee': assignee}}})
        if assignee != self.task_record['contributors']['assignee']:
            self.add_contributor(assignee)
        response = 'New assignee added to update queue.'
        return response

    def add_contributor(self, *args):
        if 'contributors 'in self.update_dictionary:
            contribs = self.update_dictionary['contributors']
        else:
            contribs = self.task_record['contributors']['additional']
        if contribs is None:
            contribs = []
        for a in args:
            if a not in contribs:
                contribs.append(a)
        try:
            pending = self.update_dictionary['contributors']
            pending['additional'] = contribs
        except KeyError:
            pending = {'additional': contribs}
        self.update_dictionary.update({'contributors': pending})
        response = 'New contributors added to update queue.'
        return response

    def del_contributor(self, *args):
        contribs = self.task_record['contributors']['additional']
        if contribs is None:
            return 'No contributors to delete!'
        else:
            for a in args:
                if a in contribs:
                    contribs.remove(a)
        try:
            pending = self.update_dictionary['contributors']
            pending['additional'] = contribs
        except KeyError:
            pending = {'additional': contribs}
        self.update_dictionary.update({'contributors': pending})
        response = 'Modified contributor list added to update queue.'
        return response

    def change_stage(self, step=1, target=None):
        '''
        Moves along the workflow stages.
        Step defaults to 1 and moves to the next stage, target chooses a specific stage.
        Open stages start at 0 and increase, closed stages start at 100 (successfully completed) and decrease
        '''
        if self.task_record['open'] and target is None:
            self.stage += step
            try:
                new_stage = self.flow.open_stages[self.stage]
            except KeyError:
                new_stage = self.flow.closed_stages[100]
                self.stage = 100
                self.update_dictionary.update({'open': False})
        elif self.task_record['open']:
            self.stage = target
            try:
                new_stage = self.flow.open_stages[target]
                self.update_dictionary.update({'open': True})
            except KeyError:
                try:
                    new_stage = self.flow.closed_stages[target]
                    self.update_dictionary.update({'open': False})
                except KeyError:
                    print(f'{target} is not a valid workflow step')
                    return f'{target} is not a valid workflow step'
        else:
            self.stage -= step
            try:
                new_stage = self.flow.closed_stages[self.stage]
            except KeyError:
                return f'This task is closed. Please specify what stage in the workflow you would like to return to.'
        self.update_dictionary.update({'stage': self.stage})
        response = "Stage change added to the update queue."
        return response

    def resolve(self):
        response = self.change_stage(target=100)
        return response

    def change_priority(self, new_priority):
        options = self.task_record['priorities']
        print(options)
        if str(new_priority) in options:
            self.update_dictionary.update({'priority': new_priority})
        else:
            response = 'Not a valid priority option.'
            return response
        response = f'Priority change added to update queue. New priority is {options[str(new_priority)]}'
        return response

    def add_todo(self, *args):
        todo_dict = self.task_record['todos']
        try:
            todo_id = len(self.task_record['todos']) + 1
        except TypeError:
            todo_id = 1
        for a in args:
            todo_dict[str(todo_id)] = {
                                'todo': a,
                                'assignee': self.task_record['contributors']['assignee'],
                                'done': False,
                                'due': None}
            todo_id += 1
        self.update_dictionary.update({'todos': todo_dict})
        response = ''
        return response

    def resolve_todo(self, todo):
        self.update_dictionary.update({'todos': {str(todo): {'done': True}}})
        response = ''
        return response

    def log_time(self, ):
        ...
        response = ''
        return response

    def start_clock(self, ):
        ...
        response = ''
        return response

    def stop_clock(self, ):
        response = ''
        return response
        ...

    def create_channel(self, ):
        client = r.db('Clients').table('clients').get(self.org).run(self.c)
        if client['platform'] == 'slack':
            # TODO Create a slack channel!
            response = 'Generating channel now!'
            channel = 'Generate slack channel'
            self.update_dictionary.update({'channel': channel})
            return response
        else:
            return "Sorry, it looks like you are not connected to the slack platform."

    def archive_channel(self, ):
        response = ''
        return response
        ...

    def add_comment(self, *args):
        comments = self.task_record['comments']
        comment_id_num = len(comments)
        for a in args:
            comment_id_num += 1
            new_comment = {str(comment_id_num):
                             {'user': self.user,
                              'comment': a,
                              'datetime': r.expr(datetime.now(r.make_timezone('-05:00')))
                             }
            }
            comments.append(new_comment)
        self.update_dictionary.update({'comments' : comments})
        response = 'Comment added to update queue.'
        return response

    def del_comment(self, to_delete):
        comments = self.task_record['comments']
        if comments == []:
            return 'No comments to delete!'
        else:
            for a in to_delete:
                for ix, c in enumerate(comments):
                    if str(a) in c:
                        comments.pop(ix)
        self.update_dictionary.update({'comments': comments})
        response = 'Modified comments list added to update queue.'
        return response

    def attach_file(self, ):
        response = ''
        return response

    def add_tag(self, *args):
        tags = self.task_record['tags']
        if tags == []:
            tags = []
        for a in args:
            if a not in tags:
                tags.append(a)
        self.update_dictionary.update({'tags': tags})
        response = 'New tags added to update queue.'
        return response

    def del_tag(self, *args):
        tags = self.task_record['tags']
        if tags is None:
            return 'No tags to delete!'
        else:
            for a in args:
                if a in tags:
                    tags.remove(a)
        self.update_dictionary.update({'tags': tags})
        response = 'Modified link tag added to update queue.'
        return response

    def add_link(self, *args):
        # First get full task list
        all_tasks = []
        new_links = self.task_record['links']
        if new_links is None:
            new_links = []
        bad_links = []
        for row in r.db(self.org).table('tasks').pluck('id').run(self.c):
            all_tasks.append(list(row.values())[0])
        for a in args:
            if a not in all_tasks and a != self.task_id:
                bad_links.append(a)
            elif a not in new_links:
                new_links.append(a)
        self.update_dictionary.update({'links': new_links})
        response = f'New links {new_links} created. The following links were not created (task does not exist) {bad_links}'
        return response

    def del_link(self, *args):
        links = self.task_record['links']
        if links is None:
            return 'No links to delete!'
        else:
            for a in args:
                if a in links:
                    links.remove(a)
        self.update_dictionary.update({'links': links})
        response = 'Modified link list added to update queue.'
        return response

class NewTask(Task):
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
                'open': True,
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
                'tags' : [],
                'todos' : {},
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
        self.update_dictionary = {}

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

