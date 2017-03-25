'''
'''

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError

from rtmbot.core import Plugin
from libs.admin import Admin_Updates
from sec.sec import *
from libs.defaults import *

class AdminUserPlugin(Plugin):

    def process_message(self, data):
            self.c = r.connect(DB_HOST, PORT)
            self.org = r.db(CLIENT_DB).table(CLIENT_TABLE).filter({'slackTeamID': data['source_team']}).pluck('id').max().run(self.c)['id']
            self.bot_id = r.db(CLIENT_DB).table(CLIENT_TABLE).get(self.org).run(self.c)['reorgBotID']
            self.a = Admin_Updates(self.org, data['user'], self.slack_client)

            # Check permissions
            admin = self.is_admin(data['user'])

            # COMMANDS
            command_dict = {
                # Create new objects
                'create team': self.a.create_team,
                'create group': self.a.create_group,
                'create priorities': self.a.create_priorities,
                'create workflow': self.a.create_workflow,
                # Modify existing objects,
                'modify team': self.a.modify_team,
                'modify group': self.a.modify_group,
                'modify priorities': self.a.modify_priorities,
                'modify workflow': self.a.modify_workflow
            }

            # Run through commands
            for k, v in command_dict.items():
                command = f"<@{self.bot_id}> {k}"
                bang_command = f"<!{k}"
                print(command)
                if data['text'].startswith(command):
                    if admin:
                        response = v(data['text'][len(command):].strip())
                        self.outputs.append([data['channel'], response])
                    else:
                        self.outputs.append([data['channel'], NON_ADMIN_MESSAGE])
                    break
                elif data['text'].startswith(bang_command):
                    if admin:
                        response = v(data['text'][len(bang_command):].strip())
                        self.outputs.append([data['channel'], response])
                    else:
                        self.outputs.append([data['channel'], NON_ADMIN_MESSAGE])
                    break
            self.c.close()
            print("DB connection closed")

    def is_admin(self, user):
        return r.db(self.org).table(USER_TABLE).get(user).run(self.c)['admin']

