from dotenv import load_dotenv
_ = load_dotenv()

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

tool = TavilySearchResults(max_results=2)

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string(":memory:")   

class Agent:
    def __init__(self, model, tools, checkpointer, system=""):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges("llm", self.exists_action, {True: "action", False: END})
        graph.add_edge("action", "llm")
        self.graph = graph.compile(checkpointer=checkpointer)
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)
    
    def call_openai(self, state: AgentState):
        print("call_openai called")
        messages = state['messages']
        if self.system:
            messages = SystemMessage(content=self.system) + messages
        message = self.model.invoke(messages)
        print("Model invoked, message:", message)
        return {'messages': [message]}
    
    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        print("exists_action called, tool calls:", result.tool_calls)
        return len(result.tool_calls) > 0
    
    def take_action(self, state: AgentState):
        print("take_action called")
        tool_calls = state['messages'][-1].tool_calls
        results=[]
        for t in tool_calls:
            print(f"Calling: {t}")
            result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}

prompt = """You are a smart research assistant. Use the search engine to look up information. \
You are allowed to make multiple calls (either together or in sequence). \
Only look up information when you are sure of what you want. \
If you need to look up some information before asking a follow up question, you are allowed to do that!
"""


model = ChatOpenAI(model="gpt-4o")
abot = Agent(model, [tool], system=prompt, checkpointer=memory)

messages = [HumanMessage(content="What is the weather in sf?")]
thread = {"configurable": {"thread_id": 1}}

for event in abot.graph.stream({"messages": messages}, thread):
    print("Event:", event)
    for v in event.values():
        print(v['messages'])

messages = [HumanMessage(content="What about in la?")]
thread = {"configurable": {"thread_id": "1"}}
for event in abot.graph.stream({"messages": messages}, thread):
    print("Event:", event)
    for v in event.values():
        print(v)

messages = [HumanMessage(content="Which one is warmer?")]
thread = {"configurable": {"thread_id":"1"}}
for event in abot.graph.stream({"messages": messages}, thread):
    print("Event:", event)
    for v in event.values():
        print(v)
