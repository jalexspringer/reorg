# ReOrg: Straightforward project management with an open interface and workflow automation
## Bringing CI/CD concepts to workflow management.
### Problem: Existing project management solutions lack integration with the activities actually required to complete tasks
### Solution: 
1. Make the workflow the central aspect and incorporate custom plugins that trigger on stage changes.
    - For example:
    - When a task moves to review, look for attachments and autosend a review packet to a team/manager.
    - When an onboarding ticket hits 'Tech Verification' run automated traffic checks, record results, notify operations teams of any needed actions.
2. Eliminate context switching by making it easy to review, update, and log time for tasks right from Slack or similar tools.
### Technology:
- Written in Python
- Built to be extensible - plugins can be used to interact with any third party tool with an API.
- RethinkDB NoSQL database
- Slack interface using the python-rtmbot framework.
- Mobile and web apps

### I/O
- Conversational style - "I completed xxx"
- Communicate with managers and record comms
- Eliminate flood of messages in inboxes and slack channels
- Export team info into reporting (time spent, productivity, etc)
- Realtime notifications using the RethinkDB architecture
- Scalable - add teams, orgs, etc.
