#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' LLM Agent nodes and utilities '''

import os
import functools
from typing import TypedDict, Sequence, Annotated
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

google_api_key = os.environ['GOOGLE_API_KEY']
model_name = os.environ.get('GOOGLE_GEMINI_MODEL', 'models/gemma-3-27b-it')
# llm with gemini model
llm = ChatGoogleGenerativeAI(
    model=model_name,
    google_api_key=google_api_key,
    temperature=0, max_tokens=None, timeout=None, max_retries=2,
)
MAX_TOKEN_LIMIT = 25_000

class AgentState(TypedDict):
    ''' State for LLM agent '''
    latest_message: Sequence[BaseMessage]
    agent_history: Annotated[Sequence[BaseMessage], lambda x, y: x + list(y)]
    option: str 

def agent_history_maintainer_node(state: AgentState, limit_tokens: int = MAX_TOKEN_LIMIT):
    ''' Maintains the agent history within token limits '''
    history = state["agent_history"]
    combined_content = " ".join([msg.content for msg in history])
    def approximate_token_count(text: str) -> int:
        # Simple token count approximation (assuming 1 token ~ 4 characters)
        return len(text) // 4
    while approximate_token_count(combined_content) > limit_tokens and history:
        oldest_msg = history.pop(0)
        combined_content = " ".join([msg.content for msg in history])
    # print(approximate_token_count(combined_content))
    state["agent_history"] = history
    return state

def generative_agent_node(state: AgentState, agent, name: str):
    """ Standard wrapper to execute a chain and update history """
    # Map AgentState to the prompt's expected input variables
    inputs = {
        "agent_history": state["agent_history"],
        "latest_message": state["latest_message"]
    }
    result = agent.invoke(inputs)
    return {
        "agent_history": [result], 
        "latest_message": [result]
    }

system_prompt_header = (
    "You are a conversational assistant running inside a Discord bot. "
    "Multiple users may talk to you in the same conversation. "
    "Each user message follows the format: "
    "'Name: <user_name>: Message: <user_message>'. "
    "Treat each user individually based on the name provided. "
    "Be friendly, light-hearted, but less enthusiastic. "
    "Avoid sarcastic, dismissive, or attitude-heavy tones."
)
chat_prompt = ChatPromptTemplate.from_messages([
    ("human", system_prompt_header),
    MessagesPlaceholder(variable_name="agent_history"),
    MessagesPlaceholder(variable_name="latest_message"),
])

simple_conversation_agent = chat_prompt | llm

# The node function you will use in the graph
simple_conversation_node = functools.partial(
    generative_agent_node,
    agent=simple_conversation_agent,
    name="SimpleConversation"
)




