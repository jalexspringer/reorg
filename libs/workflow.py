
class Workflow:
    def __init__(self, flowlist=None, name='default'):
        self.open_stages = {}
        self.closed_stages = {}
        if flowlist is None:
            flowlist = '[Open,In-Progress,Blocked,|,Completed,Cancelled,Non-Responsive]'
        else:
            flowlist = flowlist.replace(', ', ',')
        try:
            workflow = flowlist.strip('[]').split(',|,')
            for ix, s in enumerate(workflow[0].split(',')):
                self.open_stages[ix] = s
            for ix, s in enumerate(workflow[1].split(',')):
                self.closed_stages[100 - ix] = s
        except IndexError as e:
            print(e)
            try:
                workflow = flowlist.strip('[]').split(',')
                for ix, s in enumerate(workflow[:-1]):
                    self.open_stages[ix] = s
                self.closed_stages[100] = workflow[-1]
            except IndexError:
                self.open_stages = {0: 'Open', 1: 'In-Progress', 2: 'Blocked'}
                self.closed_stages = {100: 'Completed', 99: 'Cancelled', 98: 'Non-Responsive'}

        self.name = name
        # self.open_count = len(open_stages)
        # self.closed_count = len(closed_stages)
        self.flowlist = self.update_flowlist()

    def do(self, new_stage, task_id):
        for s in self.open_stages:
            if new_stage == s:
                # Fire new stage action
                ...

        for s in self.closed_stages:
            if new_stage == s:
                # Fire closed stage action
                ...

    def update_flowlist(self):
        storage = '['
        for k, s in self.open_stages.items():
            storage += s.strip() + ','
        storage += '|,'
        for k, s in self.closed_stages.items():
            storage += s.strip() + ','
        storage = storage[:-1] + ']'
        return storage
