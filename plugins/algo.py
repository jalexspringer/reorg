import yaml
import traceback
import pprint as pp

CONFIG = yaml.load(open("rtmbot.conf", "r"))

outputs = []

def process_message(data):

    pp.pprint(data)
