#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' LLM agent setup: model, system prompt, history utilities '''

#-------------------------------------------------------------------------------

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage

google_api_key = os.environ['GOOGLE_API_KEY']

_llm_kwargs = dict(
    google_api_key=google_api_key,
    temperature=0.7,
    max_tokens=1024,
    timeout=30,
    max_retries=0,  # We handle fallback ourselves — don't let langchain retry on rate limits
)

_google_search = [{'google_search': {}}]

# gemini-2.5-flash-lite: 30 RPM / 1500 RPD free tier, 1M token context window
llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite', **_llm_kwargs).bind_tools(_google_search)

# Reserve ~28K for output, system prompt, and current message
MAX_HISTORY_TOKENS = 900_000

SYSTEM_MESSAGE = SystemMessage(content=(
    "You are GO-4, a helpful assistant in a Discord server. "
    "Be friendly and conversational, but keep responses concise — "
    "Discord messages have a 2000 character limit, so avoid long walls of text. "
    "Multiple users may be active in the same conversation. "
    "Each user message is prefixed with their name: '[Username]: message'. "
    "Address users by name when it feels natural. "
    "Do NOT prefix your own responses with your name or any label like '[GO-4]:'. Just reply directly. "
    "You have access to Google Search — use it for current events, news, live data, "
    "or anything that may have changed recently. When citing search results, mention the source briefly."
))

def approximate_tokens(messages: list) -> int:
    """Rough token estimate: 1 token ≈ 4 characters."""
    return sum(len(str(msg.content)) for msg in messages) // 4

def trim_history(history: list, max_tokens: int = MAX_HISTORY_TOKENS) -> list:
    """Drop oldest messages until history fits within the token budget."""
    while history and approximate_tokens(history) > max_tokens:
        history = history[1:]
    return history
