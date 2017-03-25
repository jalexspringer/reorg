import random
import string

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError, ReqlNonExistenceError

from rtmbot.core import Plugin
from libs.admin import Admin_Updates
from sec.sec import *
from libs.defaults import *

class NewClientPlugin(Plugin):
    def process_message(self, data):
        if data['text'].startswith('init new org'):
            self.outputs.append([data['channel'], "Welcome to ReOrg! Initializing your team's database. This may take a minute if your team has a large number of members."])
            users = self.slack_client.api_call("users.list")
            team = self.slack_client.api_call("team.info")
            if team['ok']:
                team_id = team['team']['id']
                team_name = team['team']['name'].strip()
                team_domain = team['team']['domain']
                if users['ok']:
                    user_list = []
                    for u in users['members']:
                        if u['name'] == BOT_NAME:
                            reorg_bot_id = u['id']
                        elif u['is_bot'] or u['deleted'] or u['is_restricted'] or u['is_ultra_restricted'] or u['name'] == 'slackbot':
                            print(u['id'], "Skipped")
                        else:
                            user_list.append(u['id'])
                    self.account_registered(team_name, data['user'], team_id, team_domain, user_list, reorg_bot_id)
                else:
                    self.outputs.append([data['channel'], "Failed to add users. Response not OK"])
            else:
                self.outputs.append([data['channel'], "Failed to add team. Response not OK"])
            self.outputs.append([data['channel'], "New team created!"])
        else:
            print(data)


    def new_org(self, c, orgID=False):
        # Create a new database and tables for the new client.
        if orgID:
            print('User supplied orgID')
        else:
            id_len=20 # Explicitly set orgID length
            orgID = ''.join(random.choices(string.ascii_uppercase + string.digits, k=id_len))
        # Confirm unique orgID:
        try:
            r.db_create(orgID).run(c)
            r.db(orgID).table_create(USER_TABLE).run(c)
            r.db(orgID).table_create(TEAMS_TABLE).run(c)
            r.db(orgID).table_create(GROUPS_TABLE).run(c)
            r.db(orgID).table_create(TASKS_TABLE).run(c)
            print(f'New Client DB Created: {orgID}')
        except RqlRuntimeError:
            print(f'Duplicate OrgID: {orgID}, finding a new one')
            return new_org(c)
        return orgID

    def account_registered(self, client, admin_user, team_id, team_domain, user_list, reorg_bot_id):
        # Adds new client admin details to Clients DB
        # TODO Create the slack_client object to get user info.
        # TODO Keep this sucker open - allow for easy API use outside of slack as well.
        c = r.connect(DB_HOST, PORT)
        orgID = self.new_org(c)
        c_table = r.db(CLIENT_DB).table(CLIENT_TABLE)
        new_record = {
            'id': orgID,
            'name': client,
            'adminUser': admin_user,
            'slackTeamID': team_id,
            'slackTeamName': client,
            'slackTeamDomain': team_domain,
            'dbSize': '',
            'queriesPerMonth': '',
            'plan': 1,
            'teams': [(client[:3].upper().strip(), client)],
            'defaultTeams': 'all',
            'userGroups': {'GTM': 'General Team Member'},
            'defaultUserGroups': 'all',
            'reorgBotID': reorg_bot_id,
            'billing': {}
        }
        c_table.insert(new_record).run(c)
        c.close()
        a = Admin_Updates(orgID, admin_user, self.slack_client)
        for t in a.default_teams:
            a.create_team(t[0], t[1])
        for k,v in a.default_user_group.items():
            a.create_group(k, v)
        a.add_all_users(user_list)
        return orgID
