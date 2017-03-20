'''
Admin only tools to modify/add teams, users, and usergroups.
Define team template tasks, workflows, and priorities
'''

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError

from rtmbot.core import Plugin
from libs.admin import Admin_Updates
from sec.sec import *
from libs.defaults import *

class AdminUserPlugin(Plugin):

    def process_message(self, data):
            # COMMANDS
            command_dict = {
                # Create new objects
                'create team': self.new_team,
                'create group': self.new_group,
                'create priorities': self.new_priorities,
                'create workflow': self.new_workflow,
                # Modify existing objects,
                'modify team': self.modify_team,
                'modify group': self.modify_group,
                'modify priorities': self.modify_priorities,
                'modify workflow': self.modify_workflow
            }
            self.c = r.connect(DB_HOST, PORT)
            self.org = r.db(CLIENT_DB).table(CLIENT_TABLE).filter({'slackTeamID': data['source_team']}).pluck('id').max().run(self.c)['id']
            self.bot_id = r.db(CLIENT_DB).table(CLIENT_TABLE).get(self.org).run(self.c)['reorgBotID']

            # Check permissions
            admin = self.is_admin(data['user'])

            # Run through commands
            for k, v in command_dict.items():
                command = f"<@{self.bot_id}> {k}"
                print(command)
                if data['text'].startswith(command):
                    if admin:
                        response = v(data['text'][len(command):].strip())
                        self.outputs.append([data['channel'], response])
                    else:
                        self.outputs.append([data['channel'], NON_ADMIN_MESSAGE])
                    break
            self.c.close()
            print("DB connection closed")

    def get_bot_id(self):
        # find bot id
        ...

    def is_admin(self, user):
        return r.db(self.org).table(USER_TABLE).get(user).run(self.c)['admin']

    # Create new objects
    def new_team(self, command):
        return f"GOOOO TEAM! My ID is {self.bot_id}. \n I'll go ahead and create team {command}"

    def new_group(self, command):
        ...

    def new_priorities(self, command):
        ...

    def new_workflow(self, command):
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
