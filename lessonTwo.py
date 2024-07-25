from dotenv import load_dotenv
_ = load_dotenv()

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

from prompts.research_assistant import prompt

tool = TavilySearchResults(max_results=4)
print(type(tool))
print(tool.name)

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class Agent:
    def __init__(self, model, tools, system=""):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_actions)  # Updated to call `take_actions` method
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_openai(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        print(f"Model response: {message}")  # Debugging statement
        return {'messages': [message]}

    def take_actions(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling tool: {t['name']} with args: {t['args']}")  # Debugging statement
            if not t['name'] in self.tools:
                print("\n... bad tool name ...")
                result = "bad tool name, retry"
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
            print("Tool response: ", result)  # Debugging statement
        return {'messages': results}  # Updated to process all tool calls

model = ChatOpenAI(model="gpt-3.5-turbo")  # reduce inference cost
abot = Agent(model, [tool], system=prompt)

messages = [HumanMessage(content="What is the weather in SF?")]
result = abot.graph.invoke({'messages': messages})

print(result['messages'][-1].content)

messages = [HumanMessage(content="What is the weather in SF and LA?")]
result = abot.graph.invoke({'messages': messages})

print(result['messages'][-1].content)

query = "Who won the Super Bowl in 2024? In what state is the winning team headquarters located? What is the GDP of that state? Answer each question."
messages = [HumanMessage(content=query)]
abot = Agent(model, [tool], system=prompt)
result = abot.graph.invoke({'messages': messages})

print(result['messages'][-1].content)
