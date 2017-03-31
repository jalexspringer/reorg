# Global Default Settings
BOT_NAME = 'reorg'
CLIENT_DB = 'Clients'
CLIENT_TABLE = 'clients'

USER_TABLE = 'users'
TEAMS_TABLE = 'teams'
GROUPS_TABLE = 'groups'
TASKS_TABLE = 'tasks'
WORKFLOWS_TABLE = 'workflows'

DEFAULT_PRIORITIES= {'0': 'Urgent', '1': 'High', '2': 'Medium', '3': 'Low'}
DEFAULT_FLOWLIST = '[Open,In-Progress,Blocked,|,Completed,Cancelled,Non-Responsive]'

# Messaging
NON_ADMIN_MESSAGE = "This action - {} - requires admin privileges. Please contact your team admin."

# Slack Commands
COMMAND_DICTIONARY = {
    'add': {
            'contributor':'add_contributor',
            'contrib':'add_contributor',
            'todo':'add_todo',
            'time':'log_time',
            'comment':'add_comment',
            'file':'attach_file',
            'tag':'add_tag',
            'link':'add_link',
        },

    'assign': {
            'task':'assign_task',
            'todo':'assign_todo',
        },

    'del': {
            'contributor':'del_contributor',
            'contrib':'del_contributor',
            'comment':'del_comment',
            'tag':'del_tag',
            'link':'del_link',
        },

    'stage' : {
            'stage':'change_stage',
            'resolve':'resolve',
            'todo':'resolve_todo',
        },

    'admin' : {
            # Create new objects
            'create:team': 'create_team',
            'create:group': 'create_group',
            'create:priorities': 'create_priorities',
            'create:workflow': 'create_workflow',
            # Modify existing objects,
            'modify:team': 'modify_team',
            'modify:group': 'modify_group',
            'modify:priorities': 'modify_priorities',
            'modify:workflow': 'modify_workflow'
        },

    'time' : {
            'log':'log_time',
            'add':'log_time',
            'start':'start_clock',
            'stop':'stop_clock',
        },

    'list' : {
            'tasks': 'my_tasks',
            'todos': 'my_todos',
            'all': 'tasks_and_todos',
            'details': 'task_details'
        }
    }
