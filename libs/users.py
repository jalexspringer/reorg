'''
Defines User class with basic task manipulation functions
Admin user extends this and adds admin only functions to modify/add teams, users, and usergroups.
Define team template tasks, workflows, and priorities
bot_client currently calls the slack API
'''
from datetime import datetime

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError

from rtmbot.core import Plugin
from sec.sec import *
from libs.defaults import *
from libs.workflow import Workflow
from libs.task import Task, NewTask


class ReOrgUser:
    def __init__(self, org, user):
        # TODO Add timezone options and modify lastModified in dictionaries.
        self.org = org
        self.user = user
        self.admin = False
        self.c = r.connect(DB_HOST, PORT)
        res = r.db('Clients').table('clients').get(org).run(self.c)
        self.platform = res['platform']['name']
        if res['defaultTeams'] == 'all':
            self.default_teams = res['teams']
        else:
            self.default_teams = res['defaultTeams']
        if res['defaultUserGroups'] == 'all':
            self.default_user_group = res['userGroups']
        else:
            self.default_user_group = res['defaultUserGroups']

    def non_admin_response(self, command):
        return NON_ADMIN_MESSAGE.format(command)

    def start_new_task(self, title, description=None, team=None, template=None):
        t = NewTask(self.org, title, self.user, description=description, template=template, team=team)
        return t

    def open_task(self, task_id):
        return Task(self.org, task_id, self.user)

    # Queries
    def make_query(self, q_table=TASKS_TABLE):
        c = r.connect(DB_HOST, PORT)
        q_table = r.db(self.org).table(q_table)
        return c, q_table

    def my_tasks(self, **kwargs):
        c, t_table = self.make_query()
        task_response = list(t_table.filter(
            {'contributors' : {'assignee': self.user}, 'open': True}
            ).pluck('id', 'title', 'stage', {'time': ['deadline']}, 'todos'
                ).run(c))
        return task_response

    def my_todos(self, **kwargs):
        c, t_table = self.make_query()
        todo_response = list(t_table.filter(
            lambda task: (task['contributors']['additional'].contains(self.user))
            & (task['open'] == True)
            ).pluck('id', 'title', 'stage', {'time': ['deadline']}, 'todos'
                ).run(c))
        return todo_response

    def task_details(self, task_id, **kwargs):
        c, t_table = self.make_query()
        response = t_table.get(task_id).run(c)
        del response['history']
        return response


class AdminUser(ReOrgUser):
    def __init__(self, org, user):
        ReOrgUser.__init__(self, org, user)
        self.admin = True

    # Functions to create or modify
    def create_user(self, user_info, admin=False, slack=False):
        '''
        Creates new user dictionaries based on the user_info dictionary.
        Required user_info fields:
        {
        'id': unique user id,
        'profile': {
            'real_name': user name,
            'email': email,
            }
        }

        profile can also include first and last name
        '''
        # Omit deleted and bot users.
        try:
            if user_info['deleted'] or user_info['user']['is_bot'] or user_info['user']['is_restricted']:
                return None
        except:
            pass

        try:
            if user_info['is_admin'] or self.user == user:
                admin = True
        except:
            admin = False

        try:
            firstName = user_info['profile']['first_name'],
            lastName = user_info['profile']['last_name'],
        except KeyError:
            firstName = ''
            lastName = ''

        if slack:
            password = 'slackLogin'
        else:
            # TODO Send welcome emails and require password on first login.
            password = ''

        new_user = {
            'firstName': firstName,
            'lastName': lastName,
            'name': user_info['profile']['real_name'],
            'email': user_info['profile']['email'],
            'pass': password,
            'admin': admin,
            'notification': 1,
            'teams': self.default_teams,
            'dmChannel': '',
            'userGroup': self.default_user_group,
            'lastModified': r.expr(datetime.now(r.make_timezone('-05:00'))),
            'modifiedBy': self.user,
            'activityLogs': []
        }

        if slack:
            new_user.update({'id': user_info['id']})

        return new_user

    def add_all_users(self, user_array, admin=False, slack=False):
        to_insert = []
        for user in user_array:
            to_insert.append(self.create_user(user, admin=admin, slack=slack))
        try:
            c = r.connect(DB_HOST, PORT)
            r.db(self.org).table(USER_TABLE).insert(to_insert).run(c)
            return 'User created'
        except RqlRuntimeError:
            return f'Duplicate User. Use update function to make changes to an existing user.'

    # Create new objects
    def create_team(self, team_id, team_name):
        command_string = f'id={team_id} name={team_name}'
        new_team = self.parse_team_creation(command_string)
        try:
            c = r.connect(DB_HOST, PORT)
            r.db(self.org).table(TEAMS_TABLE).insert(new_team).run(c)
            return f'Team {team_id}: {team_name} created'
        except RqlRuntimeError:
            return f'Duplicate team: {team_id}. Use update function to make changes to an existing team, or try again with a unique team id.'

    def parse_team_creation(self, command):
        workflow = 'default'
        priorities = DEFAULT_PRIORITIES
        team_lead = self.user
        com_array = command.split(' ')
        for com in com_array:
            if com.startswith('id='):
                team_id=com[3:]
            elif com.startswith('name='):
                team_name=com[5:]
            elif com.startswith('manager='):
                team_lead = com[10:-1]
            elif com.startswith('workflow='):
                workflow = com[9:]
            elif com.startswith('priorities='):
                priorities = {}
                priority_names = com[11:].strip('[]').split(',')
                i = 0
                for p in priority_names:
                    priorities[str(i)] = p
                    i += 1
        try:
            new_team = {
                'id': team_id,
                'teamLead': team_lead,
                'teamName': team_name,
                'teamChannel': '',
                'templateTask': [],
                'taskCount': 0,
                'defaultWorkflow' : workflow,
                'customFields': [],
                'lastModified': r.expr(datetime.now(r.make_timezone('-05:00'))),
                'modifiedBy': self.user,
                'priorities': priorities
            }
            return new_team
        except NameError as e:
            return f'It looks like we are missing a team ID and/or name! Please use the following format `create team id=TEAMID name=TEAMNAME`. I recommend keeping the ID short (3/4 letters) and memorable.'

    def create_group(self, group_name, group_long, group_lead=None, default_team=None, permissions=1):
        c = r.connect(DB_HOST, PORT)

        # Check current group names to prevent dupes
        current_groups = []
        for row in r.db(self.org).table(GROUPS_TABLE).pluck("group_name").run(c):
            current_groups.append(row)
        if group_name in current_groups:
            return f'Duplicate group: {group_name}. Use update function to make changes to an existing usergroup, or try again with a unique usergroup name.'

        # All good - new name
        else:
            if default_team:
                res = r.db(self.org).table(TEAMS_TABLE).get(default_team).run(c)
                if res is not None:
                    default_team = default_team
                else:
                    print('No such team. Switching to default. Change with update usergroup.')
                    default_team = self.default_teams[0][0]
            else:
                default_team = self.default_teams[0][0]
            try:
                group_ids = r.db(self.org).table(GROUPS_TABLE).pluck('id').max().run(c)
                group_id = group_ids['id'] + 1
            except ReqlNonExistenceError:
                group_id = 1
            new_group = {
                'id' : group_id,
                'groupName': group_name,
                'defaultTeam': default_team,
                'groupLongName': group_long,
                'groupLead' : group_lead,
                'lastModified': r.expr(datetime.now(r.make_timezone('-05:00'))),
                'modifiedBy': self.user,
                'defaultPermissions' : permissions
            }
            r.db(self.org).table(GROUPS_TABLE).insert(new_group).run(c)
            return 'Group created'

    def create_workflow(self, flowlist=None, name='default'):
        # Flow list format: '[Open,Working,|,Closed,Cancelled]'
        # If no pipe is sent then the last stage is considered the only closed stage.
        c = r.connect(DB_HOST, PORT)
        flow = Workflow(flowlist, name)
        new_flow = {
            'id': flow.name,
            'flowlist': flow.flowlist,
            'lastModified': r.expr(datetime.now(r.make_timezone('-05:00'))),
            'modifiedBy': self.user,
        }
        res = r.db(self.org).table('workflows').insert(new_flow).run(c)
        c.close()
        return flow.name

    def create_priorities(self, command):
        ...

    # Modify existing objects,
    def modify_team(self, command):
        return "You modify that team."
        ...

    def modify_group(self, command):
        ...

    def modify_priorities(self, command):
        ...

    def modify_workflow(self, command):
        ...

    # Information requests
    def full_name(self, user_id):
        name = r.db(self.org).table(USER_TABLE).get(user_id).run(self.c)['name']
        return name

    def stage_name(self, workflow, stage):
        flowlist = r.db(self.org).table(WORKFLOWS_TABLE).get(workflow).run(self.c)['flowlist']
        w = Workflow(flowlist, workflow)
        if stage < 50:
            return w.open_stages[stage]
        else:
            return w.closed_stages[stage]
