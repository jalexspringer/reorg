
class Workflow:
    def __init__(self, flow_list=None, name='reorgDefault'):
        if flow_list is None:
            flow_list = '[Open,In-Progress,Blocked,|,Completed,Cancelled,Non-Responsive]'
        else:
            flow_list = flow_list.replace(', ', ',')
        try:
            workflow = flow_list.strip('[]').split(',|,')
            self.open_stages = workflow[0].split(',')
            self.closed_stages = workflow[1].split(',')
        except IndexError as e:
            print(e)
            try:
                workflow = flow_list.strip('[]').split(',')
                self.open_stages = workflow[:-1]
                self.closed_stages = workflow[-1:]
            except IndexError:
                self.open_stages = None
                self.closed_stages = None
        if self.open_stages is None:
            self.open_stages = ['Open', 'In-Progress', 'Blocked']
        if self.closed_stages is None:
            self.closed_stages = ['Completed', 'Cancelled' 'Non-Responsive']

        self.name = name
        # self.open_count = len(open_stages)
        # self.closed_count = len(closed_stages)
        self.flow_list = self.update_flow()

    def do(self, new_stage):
        for s in self.open_stages:
            if new_stage == s:
                # Fire new stage action
                ...

        for s in self.closed_stages:
            if new_stage == s:
                # Fire closed stage action
                ...

    def update_flow(self):
        storage = '['
        for s in self.open_stages:
            storage += s.strip() + ','
        storage += '|,'
        for s in self.closed_stages:
            storage += s.strip() + ','
        storage = storage[:-1] + ']'
        return storage
