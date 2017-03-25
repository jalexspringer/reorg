'''
'''

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError

from rtmbot.core import Plugin
from libs.users import AdminUser, ReOrgUser
from sec.sec import *
from libs.defaults import *

class AdminUserPlugin(Plugin):

    def process_message(self, data):
            self.c = r.connect(DB_HOST, PORT)
            self.org = r.db(CLIENT_DB).table(CLIENT_TABLE).filter({'platform':{'slackTeamID': data['source_team']}}).pluck('id').max().run(self.c)['id']
            self.bot_id = r.db(CLIENT_DB).table(CLIENT_TABLE).get(self.org).run(self.c)['platform']['reorgBotID']

            # General user command dict
            command_dict = {

            }
            # Check permissions and create appropriate User object
            admin = self.is_admin(data['user'])
            if admin:
                u = AdminUser(self.org, data['user'])
                admin_commands = {
                    # Create new objects
                    'create team': u.create_team,
                    'create group': u.create_group,
                    'create priorities': u.create_priorities,
                    'create workflow': u.create_workflow,
                    # Modify existing objects,
                    'modify team': u.modify_team,
                    'modify group': u.modify_group,
                    'modify priorities': u.modify_priorities,
                    'modify workflow': u.modify_workflow
                }
                command_dict.update(admin_commands)
            else:
                u = ReOrgUser(self.org, data['user'])
                admin_commands = {
                    # Create new objects
                    'create team': u.non_admin_response,
                    'create group': u.non_admin_response,
                    'create priorities': u.non_admin_response,
                    'create workflow': u.non_admin_response,
                    # Modify existing objects,
                    'modify team': u.non_admin_response,
                    'modify group': u.non_admin_response,
                    'modify priorities': u.non_admin_response,
                    'modify workflow': u.non_admin_response,
                }
                command_dict.update(admin_commands)

            # Run through commands
            for k, v in command_dict.items():
                command = f"<@{self.bot_id}> {k}"
                bang_command = f"!{k}"
                if data['text'].startswith(command):
                    response = v(data['text'][len(command):].strip())
                    self.outputs.append([data['channel'], response])
                elif data['text'].startswith(bang_command):
                    response = v(data['text'][len(bang_command):].strip())
                    self.outputs.append([data['channel'], response])
            self.c.close()
            print("DB connection closed")

    def is_admin(self, user):
        return r.db(self.org).table(USER_TABLE).get(user).run(self.c)['admin']

