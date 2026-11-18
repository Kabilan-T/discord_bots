#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Shared text to speech helpers (edge-tts voices + Tanglish to Tamil script) '''

#-------------------------------------------------------------------------------

import os
import re
import uuid
import asyncio
import aiohttp
import edge_tts

tmp = "tmp"

# EVE's own voice (greet, say via GO-4, anything EVE says by herself)
EVE_VOICE = "ta-IN-PallaviNeural"
# Voices handed out to people using say, in order (male / female alternating)
USER_VOICES = [
    ("Kumar", "ta-LK-KumarNeural"),
    ("Venba", "ta-SG-VenbaNeural"),
    ("Surya", "ta-MY-SuryaNeural"),
    ("Kani", "ta-MY-KaniNeural"),
    ("Anbu", "ta-SG-AnbuNeural"),
    ("Saranya", "ta-LK-SaranyaNeural"),
    ("Valluvar", "ta-IN-ValluvarNeural"),
]
# M-O's voice
MO_VOICE = "en-IN-PrabhatNeural"

XLIT_URL = "https://inputtools.google.com/request"
_xlit_cache = dict()


async def _xlit_word(session, word):
    ''' Transliterate one latin word to Tamil script; returns the word unchanged on failure '''
    key = word.lower()
    if key in _xlit_cache:
        return _xlit_cache[key]
    try:
        params = {"text": word, "itc": "ta-t-i0-und", "num": 1}
        async with session.get(XLIT_URL, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
            data = await response.json(content_type=None)
        result = data[1][0][1][0] if data[0] == "SUCCESS" else word
    except Exception:
        return word
    _xlit_cache[key] = result
    return result


async def to_tamil_script(text):
    ''' Convert Tanglish (latin letters) to Tamil script; Tamil script, numbers and symbols are kept '''
    parts = re.findall(r"[A-Za-z]+|[^A-Za-z]+", text)
    words = {p for p in parts if p.isascii() and p.isalpha()}
    if not words:
        return text
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[_xlit_word(session, w) for w in words])
    mapping = dict(zip(words, results))
    return "".join(mapping.get(p, p) for p in parts)


async def synthesize(text, voice):
    ''' Generate speech with edge-tts; returns the mp3 path (caller deletes it). Raises on failure. '''
    os.makedirs(tmp, exist_ok=True)
    file = os.path.join(tmp, f"tts_{uuid.uuid4().hex}.mp3")
    try:
        await edge_tts.Communicate(text, voice).save(file)
    except Exception:
        if os.path.exists(file):
            os.remove(file)
        raise
    if not os.path.exists(file) or os.path.getsize(file) == 0:
        raise RuntimeError("edge-tts returned no audio")
    return file


def remove_file(file):
    try:
        os.remove(file)
    except OSError:
        pass
