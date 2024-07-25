from dotenv import load_dotenv
_ = load_dotenv()

from langgraph.graph import StateGraph, END

from typing import TypedDict, Annotated
import operator
from langgraph.checkpoint.sqlite import SqliteSaver

class AgentState(TypedDict):
    lnode: str
    scratch: str
    count: Annotated[int, operator.add]

def node1(state: AgentState):
    print(f"node1, count:{state['count']}")
    return {
        "lnode":"node_1",
        "count": 1,
    }
    
def node2(state: AgentState):
    print(f"node2, count:{state['count']}")
    return {
        "lnode": "node_2",
        "count": 1,
    }

def should_continue(state):
    return state['count'] < 3


builder = StateGraph(AgentState) 
builder.add_node("Node1", node1)
builder.add_node("Node2", node2)

builder.add_edge("Node1", "Node2")
builder.add_conditional_edges("Node2", should_continue, {True: "Node1", False: END})

builder.set_entry_point("Node1")

memory = SqliteSaver.from_conn_string(":memory:")

graph = builder.compile(checkpointer=memory)

# Run it

thread = {"configurable": {"thread_id": str(1)}}
graph.invoke({"count": 0, "scratch": "hi"}, thread)

# Look at current state
graph.get_state(thread)

# Look at state history

for state in graph.get_state_history(thread):
    print(state, "\n")

states = []
for state in graph.get_state_history(thread):
    states.append(state.config)
    print(state.config, state.values['count'])

# Grab an early state

print(states[-3])

graph.get_state(states[-3])

# Go back in time

graph.invoke(None, states[-3])

thread = {"configurable": {"thread_id": str(1)}} 
for state in graph.get_state_history(thread):
    print(state.config, state.values['count'])

thread = {"configurable": {"thread_id" : str(1)}}
for state in graph.get_state_history(thread):
    print(state, "\n")

# Modify state
thread2 = {"configurable": {"thread_id": str(2)}}
graph.invoke({"count": 0, "scratch": "hi"}, thread2)

from IPython.display import Image

Image(graph.get_graph().draw_png())

states2 = []
for state in graph.get_state_history(thread2):
    states2.append(state.config)
    print(state.config, state.values['count'])

#Start by grabbing a state
save_state = graph.get_state(states2[-3])
print(save_state)

save_state.values['count'] = -3
save_state.values['scratch'] = "hello"
print(save_state)

graph.update_state(thread2, save_state.values)

for i, state in enumerate(graph.get_state_history(thread2)):
    if i >= 3: # print latest 3
        break
    print(state, '\n')

graph.update_state(thread2, save_state.values, as_node="Node1")

for i, state in enumerate(graph.get_state_history(thread2)):
    if i >= 3:
        break
    print(state, '\n')

graph.invoke(None, thread2)

for state in graph.get_state_history(thread2):
    print(state, '\n')



    