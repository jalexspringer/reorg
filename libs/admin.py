'''
Admin only tools to modify/add teams, users, and usergroups.
Define team template tasks, workflows, and priorities
bot_client currently calls the slack API
'''
from datetime import datetime

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError

from rtmbot.core import Plugin
from sec.sec import *
from libs.defaults import *

class Admin_Updates():
    def __init__(self, org, admin_user, bot_client):
        self.org = org
        self.admin_user = admin_user
        self.bot_client = bot_client
        c = r.connect(DB_HOST, PORT)
        res = r.db('Clients').table('clients').get(org).run(c)
        if res['defaultTeams'] == 'all':
            self.default_teams = res['teams']
        else:
            self.default_teams = res['defaultTeams']
        if res['defaultUserGroups'] == 'all':
            self.default_user_group = res['userGroups']
        else:
            self.default_user_group = res['defaultUserGroups']
        c.close()

    # Functions to create or modify
    def create_slack_user(self, user, admin=False):
        # Slack info check
        user_info = self.bot_client.api_call("users.info", user=user)
        if user_info['ok']:

            # Omit deleted and bot users.
            if user_info['user']['deleted'] or user_info['user']['is_bot'] or user_info['user']['is_restricted']:
                return None

            if user_info['user']['is_admin'] or self.admin_user == user:
                admin = True

            try:
                firstName = user_info['user']['profile']['first_name'],
                lastName = user_info['user']['profile']['last_name'],
            except KeyError:
                firstName = ''
                lastName = ''

            new_user = {
                'id': user,
                'firstName': firstName,
                'lastName': lastName,
                'name': user_info['user']['profile']['real_name'],
                'email': user_info['user']['profile']['email'],
                'pass': '',
                'admin': admin,
                'notification': 1,
                'teams': self.default_teams,
                'dmChannel': '',
                'userGroup': self.default_user_group,
                'lastModified': r.expr(datetime.now(r.make_timezone('-05:00'))),
                'modifiedBy': self.admin_user,
                'activityLogs': []
            }
            return new_user
        else:
            print(f"Slack error - check user details for user {user}")
            return None

    def add_all_users(self, user_array, admin=False):
        to_insert = []
        for user in user_array:
            to_insert.append(self.create_slack_user(user, admin=admin))
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
        workflow = DEFAULT_WORKFLOW
        priorities = DEFAULT_PRIORITIES
        team_lead = self.admin_user
        com_array = command.split(' ')
        for com in com_array:
            if com.startswith('id='):
                team_id=com[3:]
            elif com.startswith('name='):
                team_name=com[5:]
            elif com.startswith('manager='):
                team_lead = com[10:-1]
            elif com.startswith('workflow='):
                workflow = com[9:].strip('[]').split(',')
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
                'workflows' : workflow,
                'customFields': [],
                'lastModified': r.expr(datetime.now(r.make_timezone('-05:00'))),
                'modifiedBy': self.admin_user,
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
                'modifiedBy': self.admin_user,
                'defaultPermissions' : permissions
            }
            r.db(self.org).table(GROUPS_TABLE).insert(new_group).run(c)
            return 'Group created'

    def create_workflow(self, command):
        ...

    def create_priorities(self, command):
        ...

    # Modify existing objects,
    def modify_team(self, command):
        ...

    def modify_group(self, command):
        ...

    def modify_priorities(self, command):
        ...

    def modify_workflow(self, command):
        ...

'''
    def create_other_user(self, user, teams=False, usergroups=False, password=False, admin=False):
        # Auth placeholders
        import hashlib
        if password:
            m = hashlib.sha224()
            m.update(password)
            p = m.digest()
        else:
            p = ''

        # Slack info check
        user_info = self.bot_client.api_call("users.info", user=user)
        if user_info['user']['is_bot']:
            return None
        elif user_info['ok']:
            # Teams are entirely client defined. This needs to be part of the initial setup process. Default is to the first three letters of the org name.
            if user_info['user']['is_admin']:
                admin = True

            if teams:
                teams=teams
            else:
                teams = self.default_teams

            # Get user roles from Slack to populate default usergroups
            # TODO Enforce this as a dictionary - use key to check with teams and usergroups tables
            if usergroups:
                usergroups = usergroups
            else:
                usergroups = self.default_user_group

            new_user = {
                'id': user,
                'firstName': user_info['user']['profile']['first_name'],
                'lastName': user_info['user']['profile']['last_name'],
                'name': user_info['user']['profile']['real_name'],
                'email': user_info['user']['profile']['email'],
                'pass': p,
                'admin': admin,
                'notification': 1,
                'teams': teams,
                'dmChannel': '',
                'userGroup': usergroups,
                'lastModified': r.expr(datetime.now(r.make_timezone('-05:00'))),
                'modifiedBy': self.admin_user,
                'activityLogs': []
            }
            return new_user
        else:
            print(f"Slack error - check user details for user {user}")
            return None
'''
