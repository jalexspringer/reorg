from rtmbot.core import Plugin

import time

class TimerPlugin(Plugin):
    def process_message(self, data):
        if data['text'] == 'go bot go':
            self.slack_client.api_call(
                "chat.postMessage",
                channel = data['channel'],
                text = "Hello! Good to meet you! :wave:",
                attachments = [
                    {
                    "title": "Good stuff goes here.",
                    "pretext": "Subtitle, preparing the channel for the good stuff!",
                    'text': "OOOOOHHHHHH YEAH.",
                    'mrkdwn_in': [
                        'text',
                        'pretext'
                    ],
                    'actions': [
                        {
                            'name': 'first',
                            'text': 'Numba1',
                            'type': 'button',
                            'value': 'chess'
                        } ] } ]
            )
