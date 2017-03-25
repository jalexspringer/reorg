from rtmbot.core import Plugin

class CatchAllPlugin(Plugin):

    def catch_all(self, data):
        print(data)
