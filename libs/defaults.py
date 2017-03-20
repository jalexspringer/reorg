# Global Default Settings
BOT_NAME = 'reorg'
CLIENT_DB = 'Clients'
CLIENT_TABLE = 'clients'

USER_TABLE = 'users'
TEAMS_TABLE = 'teams'
GROUPS_TABLE = 'groups'

DEFAULT_WORKFLOW = ['Open', 'In-Progress', 'Blocked', '|', 'Completed', 'Cancelled']
DEFAULT_PRIORITIES= {'0': 'Urgent', '1': 'High', '2': 'Medium', '3': 'Low'}

# Messaging
NON_ADMIN_MESSAGE = "This action requires admin priveleges. Please contact your team admin."
