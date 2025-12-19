#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' LLM graph workflow utilities '''

import os
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from llm_agents import AgentState
from llm_agents import agent_history_maintainer_node
from llm_agents import simple_conversation_node

# Initialize the graph 
workflow = StateGraph(AgentState)
workflow.add_node("MaintainHistory", agent_history_maintainer_node)
workflow.add_node("SimpleChat", simple_conversation_node)

# Define the flow
workflow.add_edge(START, "MaintainHistory")
workflow.add_edge("MaintainHistory", "SimpleChat")
workflow.add_edge("SimpleChat", END)

agent_workflow = workflow.compile()

def get_agent_response(user_message: str, user_name: str, previous_state: AgentState = None):
    ''' Get response from the agent workflow '''
    user_msg = HumanMessage(content=f'Name: {user_name}: Message: {user_message}')
    initial_state = {"latest_message": [user_msg]}
    if previous_state is None:
        initial_state["agent_history"] = [user_msg]
    else:
        initial_state["agent_history"] = previous_state["agent_history"] + [user_msg]

    for step in agent_workflow.stream(initial_state):
        if "__end__" in step:
            continue
        for node, state in step.items():
            latest_responses = state.get("latest_message", [])[0].content
            latest_state = state
    return latest_responses, latest_state



if __name__ == "__main__":
    last_state = None
    while True:
        user_name = input("Enter your name: ")
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response, last_state = get_agent_response(user_input, user_name, last_state)
        print(f"Bot: {response}")
         




