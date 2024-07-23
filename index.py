import openai
import re
import httpx
import os
from dotenv import load_dotenv

_ = load_dotenv()
from openai import OpenAI
from prompts.dog_weight import prompt as dog_prompt

# MY_ENV_VAR = os.getenv('MY_ENV_VAR')

# print(MY_ENV_VAR)

client= OpenAI()


class Agent:
        def __init__(self, system=""):
                self.system = system
                self.messages = []
                if self.system:
                        self.messages.append({"role": "user", "content": system})
                        
        def __call__(self, message):
            self.messages.append({"role": "user", "content": message})
            result = self.execute()
            self.messages.append({"role": "assistant", "content": result})
            return result
        
        def execute(self):
            completion = client.chat.completions.create(
                model="gpt-4o",
                temperature=0,
                messages=self.messages)
            return completion.choices[0].message.content
        

def calculate(what):
    return eval(what)

def average_dog_weight(name):
    if name in "Scottish Terrier":
        return("Scottish Terriers average 20 lbs")
    elif name in "Border Collie":
        return("a Border Collies average weight is 37 lbs")
    elif name in "Toy Poodles":
        return("a toy poodles average weight is 7 lbs")
    else:
        return("An average dog weighs 50 lbs")
        
known_actions = {
    "calculate": calculate,
    "average_dog_weight": average_dog_weight
}

action_re = re.compile('^Action: (\w+): (.*)$')

def query(question, max_turns=5):
    i = 0
    bot = Agent(dog_prompt)
    next_prompt = question
    while i < max_turns:
        i += 1
        result = bot(next_prompt)
        print(result)
        actions = [
            action_re.match(a)
            for a in result.split('\n') 
            if action_re.match(a)
            ]
        if actions:
            #There is an action to run
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception('Unknown action: {} : {}'.format(action, action_input))
            print(" -- running {} : {}".format(action, action_input))
            observation = known_actions[action](action_input)
            print("Observation: {}".format(observation))
        
        else:
            return
        
question = """I have 2 dogs, a border collie and a scottish terrier. \
What is their combined weight"""
query(question)