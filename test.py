import time

import rethinkdb as r
from slackclient import SlackClient

from sec.sec import *
from libs.defaults import *
from libs.task import Task, NewTask
from libs.workflow import Workflow
from libs.users import AdminUser, ReOrgUser
from plugins.new_client import *

c = r.connect(DB_HOST, PORT)

def find_test_org(name):
    try:
        res = r.db('Clients').table('clients').filter({'name': name}).run(c)
        for i in res:
            org = i['id']
        return org
    except:
        return None

org = find_test_org('AS Org')

def deep_scrub(names):
    to_clean = []
    for n in names:
        to_clean.append(find_test_org(n))
    for i in to_clean:
        try:
            r.db("Clients").table("clients").get(i).delete().run(c)
            r.db_drop(i).run(c)
        except:
            pass
    res = r.db("Clients").table('clients').run(c)
    print(to_clean, 'Dropped')

deep_scrub(['AS Org'])

sc = SlackClient(SLACK_TOKEN)

sc.api_call(
    "chat.postMessage",
    channel = 'C3MS39UUS',
    text = "init new org",
    as_user=True
)

time.sleep(15)

user = 'U3NGNR04W'
org = find_test_org('AS Org')
print('Org is ', org)
a = AdminUser(org, user)
flowlist = '[Applied, Interviewing, On Hold,|, No Offer, Accepted Offer, Declined Offer]'
w = Workflow(flowlist=flowlist, name='HR flow')
a.create_workflow(w.flowlist, w.name)
for i in range(2):
    team_name = '{}Team'.format(i)
    a.create_team(team_name[:3], team_name)
    a.create_group(str(i), '{}Resources'.format(i), default_team=team_name[:3])    
    for x in range(5):
        title = '{}Task'.format(x)
        description = 'This is a task description for task {}'.format(x)
        t = NewTask(org, title, description, user, team=team_name[:3], workflow='HR flow')
        t.commit()


t = Task(org, '1Te-001', user)
t.task_record
t.assign_task('Alex')
t.add_contributor(['Josh', 'Janet'])
t.add_link(['HR-000', '1Te-002', '2Te-001'])
t.add_tag(['free_stuff', 'hirings'])
t.add_todo(['my first task', 'second, the jump', 'third!'])
t.assign_todo('Anna', 2)
t.add_comment(['Started kicking ass on this project.'])
t.add_comment(['Continued kicking ass on this project.'])
t.change_priority(2)
t.change_stage()
t.commit()

t = Task(org, '1Te-002', user)
t.task_record
t.assign_task(['Alex'])
t.add_contributor(['Josh', 'Janet'])
t.add_link(['HR-000', '1Te-002', '2Te-001'])
t.add_tag(['free_stuff', 'hirings'])
t.add_todo(['my first task', 'second, the jump', 'third!'])
t.assign_todo('Anna', 2)
t.add_comment(['Started kicking ass on this project.'])
t.add_comment(['Continued kicking ass on this project.'])
t.change_priority(2)
t.change_stage()
t.commit()

t.del_comment([1,2])
t.del_contributor(['Josh'])
t.del_link(['1Te-002'])
t.del_tag(['hirings'])
t.commit()
print(r.db(org).table('tasks').get(t.task_id).run(c))
