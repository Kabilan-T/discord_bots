#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' LLM response: direct chat with history '''

#-------------------------------------------------------------------------------

from langchain_core.messages import HumanMessage
try:
    from .llm_agents import SYSTEM_MESSAGE, llm, trim_history
except ImportError:
    from llm_agents import SYSTEM_MESSAGE, llm, trim_history

def get_agent_response(user_message: str, user_name: str, history: list = None):
    """
    Get a response from the LLM.

    Args:
        user_message:  The user's raw message text.
        user_name:     Discord display name of the sender.
        history:       List of prior LangChain messages for this session.

    Returns:
        (response_text, updated_history)
    """
    if history is None:
        history = []

    history = trim_history(list(history))

    user_msg = HumanMessage(content=f"[{user_name}]: {user_message}")
    messages = [SYSTEM_MESSAGE] + history + [user_msg]

    response = llm.invoke(messages)

    updated_history = history + [user_msg, response]
    return response.content, updated_history


if __name__ == "__main__":
    last_history = None
    user_name = input("Name: ")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response, last_history = get_agent_response(user_input, user_name, last_history)
        print(f"GO-4: {response}")
