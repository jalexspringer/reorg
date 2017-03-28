import rethinkdb as r
from sec.sec import *
from libs.defaults import *
from libs.task import Task

c = r.connect(DB_HOST, PORT)

org='5KO92E2QEA1VY41M3X4P'
user = 'U3NGNR04W'
title = 'More HR training.'
description = 'Will it never end?'

t = Task(org, 'HR-001', user)

t.task_record
t.assign_task('Alex')
t.add_contributor('Josh', 'Janet')
t.add_link('HR-000', 'HR-002')
t.add_tag('free_stuff', 'hirings')
t.task_record.update({'todos': None})
t.add_todo('my first task', 'second, the jump', 'third!')
t.add_comment('Started kicking ass on this project.')
t.add_comment('Continued kicking ass on this project.')
t.commit()
db.table('tasks').get(t.task_id).run(c)

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
t.add_contributor('Josh', 'Janet')
t.add_link('HR-000', '1Te-002', '2Te-001')
t.add_tag('free_stuff', 'hirings')
t.add_todo('my first task', 'second, the jump', 'third!')
t.assign_todo('Anna', 2)
t.add_comment('Started kicking ass on this project.')
t.add_comment('Continued kicking ass on this project.')
t.change_priority(2)
t.change_stage()
t.commit()

t = Task(org, '1Te-002', user)
t.task_record
t.assign_task('Alex')
t.add_contributor('Josh', 'Janet')
t.add_link('HR-000', '1Te-002', '2Te-001')
t.add_tag('free_stuff', 'hirings')
t.add_todo('my first task', 'second, the jump', 'third!')
t.assign_todo('Josh', 3)
t.add_comment('Started kicking ass on this project.')
t.add_comment('Continued kicking ass on this project.')
t.change_priority(2)
t.change_stage(target=100)
t.commit()

t.del_comment([1,2])
t.del_contributor('Josh')
t.del_link('1Te-002')
t.del_tag('hirings')
t.commit()
print(r.db(org).table('tasks').get(t.task_id).run(c))
