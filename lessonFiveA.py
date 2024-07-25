from dotenv import load_dotenv

_ = load_dotenv()

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string(":memory:")

from uuid import uuid4

def reduce_messages(left: list[AnyMessage], right: list[AnyMessage]) -> list[AnyMessage]:
    for message in right:
        if not message.id:
            message.id = str(uuid4())
    
    # Merge the new messages into the old messages
    merged = left.copy()
    existing_ids = {msg.id for msg in left}
    for message in right:
        if message.id in existing_ids:
            # Replace existing message with the same id
            for i, existing in enumerate(merged):
                if existing.id == message.id:
                    merged[i] = message
                    break
        else:
            # Append new message to the end
            merged.append(message)
    return merged
    
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], reduce_messages]

tool = TavilySearchResults(max_results=2)

class Agent:
    def __init__(self, model, tools, system="", checkpointer=None):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges("llm", self.exists_action, {True: "action", False: END})
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile(
            checkpointer=checkpointer,
            interrupt_before=["action"]
        )
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)
    
    def call_openai(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': messages + [message]}  # This should be message instead of messages

    def exists_action(self, state: AgentState):
        print(state)
        result = state['messages'][-1]
        return len(result.tool_calls) > 0  # Fixed the condition check
    
    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")
            result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print('Back to the model!')
        return {'messages': state['messages'] + results}
    
prompt = """You are a smart research assistant. Use the search engine to look up information. \
You are allowed to make multiple calls (either together or in sequence). \
Only look up information when you are sure of what you want. \
If you need to look up some information before asking a follow up question, you are allowed to do that!
"""
model = ChatOpenAI(model="gpt-3.5-turbo")
abot = Agent(model, [tool], system=prompt, checkpointer=memory)
        
messages = [HumanMessage(content="What's the weather in SF?")]
thread = {"configurable": {"thread_id": "1"}}
for event in abot.graph.stream({"messages": messages}, thread):
    for v in event.values():
        print(v)

abot.graph.get_state(thread)
abot.graph.get_state(thread).next


# Continue after interrupt

for event in abot.graph.stream(None, thread):
    for v in event.values():
        print(v)

abot.graph.get_state(thread)
abot.graph.get_state(thread).next

messages = [HumanMessage("What's the weather in LA?")]
thread = {"configurable": {"thread_id": "3"}}
for event in abot.graph.stream({"messages": messages}, thread):
    for v in event.values():
        print(v)

# Modify the state

messages = [HumanMessage("What's the weather in LA?")]
thread = {"configurable" : {"thread_id" : "3"}}
for event in abot.graph.stream({"messages" : messages}, thread):
    for v in event.values():
        print(v)
            
abot.graph.get_state(thread)

current_values = abot.graph.get_state(thread)
current_values.values['messages'][-1]
current_values.values['messages'][-1].tool_calls

_id = current_values.values['messages'][-1].tool_calls[0]['id']
current_values.values['messages'][-1].tool_calls = [
    {'name' : 'tavily_search_results_json', 
     'args': {'query': 'current weather in Louisiana'}, 
     'id': _id}
]

abot.graph.update_state(thread, current_values.values)
abot.graph.get_state(thread)

for event in abot.graph.stream(None, thread):
    for v in event.values():
        print(v)

# Time travel

states = [] 
for state in abot.graph.get_state_history(thread):
    print(state)
    print('--')
    states.append(state)

to_replay = states[-3]

print(to_replay)

for event in abot.graph.stream(None, to_replay.config): 
    for k,v in event.items():
        print(v)

# Go back in time and edit

print(to_replay)

_id = to_replay.values['messages'][-1].tool_calls[0]['id']
to_replay.values['messages'][-1].tool_calls = [{'name': 'tavily_search_results_json', 'args': {'query': 'current weather in LA, accuweather'}, 
                                                'id': _id }]

branch_state = abot.graph.update_state(to_replay.config, to_replay.values)

for event in abot.graph.stream(None, branch_state):
    for k, v in event.items():
        if k != '__end__':
            print(v)

# Add message to a state at a given time

print(to_replay)

_id = to_replay.values['messages'][-1].tool_calls[0]['id']
state_update = {
    "messages": [ToolMessage(
        tool_call_id = _id,
        name = 'tavily_search_results_json',
        content='54 degree celsius',
    )]}

branch_and_add = abot.graph.update_state(
    to_replay.config,
    state_update,
    as_node="action")

for event in abot.graph.stream(None, branch_and_add):
    for k, v in event.items():
        print(v)
