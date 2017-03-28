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


