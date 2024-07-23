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


chat_completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Hello World"}]
)

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

abot = Agent(dog_prompt)





abot = Agent(dog_prompt)

question = """I have 2 dogs, a border collie and a scottish terrier. \
What is their combined weight"""

abot(question)


next_prompt = "Observation: {}".format(average_dog_weight("Border Collie"))
print(next_prompt)

print(abot(next_prompt))

next_prompt = "Observation: {}".format(average_dog_weight("Scottish Terrier"))
print(next_prompt)

        

print(abot(next_prompt))

next_prompt = "Observation: {}".format(eval("37 + 20"))
print(next_prompt)


print(abot(next_prompt))

