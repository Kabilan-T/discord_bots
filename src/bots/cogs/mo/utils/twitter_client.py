#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Twitter/X client: fetch tweet status and media via the public guest GraphQL API '''

#-------------------------------------------------------------------------------

import re
import json
import requests
from urllib.parse import unquote

BEARER_TOKEN = unquote(
    'AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'
)
GRAPHQL_ENDPOINT = 'https://x.com/i/api/graphql/2ICDjqPd81tulZcYrtpTuQ/TweetResultByRestId'
USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

def extract_tweet_id(url: str):
    '''Extract the numeric tweet ID from a twitter/x status URL'''
    match = re.search(r"status/(\d+)", url)
    if not match:
        return None
    return match.group(1)

def get_guest_token(session: requests.Session) -> str:
    '''Get a fresh, anonymous guest token (no login required)'''
    response = session.post(
        'https://api.x.com/1.1/guest/activate.json',
        headers={'Authorization': f'Bearer {BEARER_TOKEN}', 'User-Agent': USER_AGENT},
        data=b'',
    )
    response.raise_for_status()
    return response.json()['guest_token']

def fetch_raw_tweet(session: requests.Session, tweet_id: str, guest_token: str) -> dict:
    '''Fetch the raw GraphQL TweetResultByRestId response for a tweet'''
    variables = {
        'tweetId': tweet_id,
        'withCommunity': False,
        'includePromotedContent': False,
        'withVoice': False,
    }
    features = {
        'creator_subscriptions_tweet_preview_api_enabled': True,
        'tweetypie_unmention_optimization_enabled': True,
        'responsive_web_edit_tweet_api_enabled': True,
        'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
        'view_counts_everywhere_api_enabled': True,
        'longform_notetweets_consumption_enabled': True,
        'responsive_web_twitter_article_tweet_consumption_enabled': False,
        'tweet_awards_web_tipping_enabled': False,
        'freedom_of_speech_not_reach_fetch_enabled': True,
        'standardized_nudges_misinfo': True,
        'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
        'longform_notetweets_rich_text_read_enabled': True,
        'longform_notetweets_inline_media_enabled': True,
        'responsive_web_graphql_exclude_directive_enabled': True,
        'verified_phone_label_enabled': False,
        'responsive_web_media_download_video_enabled': False,
        'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
        'responsive_web_graphql_timeline_navigation_enabled': True,
        'responsive_web_enhance_cards_enabled': False,
    }
    field_toggles = {'withArticleRichContentState': False}
    response = session.get(
        GRAPHQL_ENDPOINT,
        headers={
            'Authorization': f'Bearer {BEARER_TOKEN}',
            'x-guest-token': guest_token,
            'User-Agent': USER_AGENT,
        },
        params={
            'variables': json.dumps(variables, separators=(',', ':')),
            'features': json.dumps(features, separators=(',', ':')),
            'fieldToggles': json.dumps(field_toggles, separators=(',', ':')),
        },
    )
    response.raise_for_status()
    return response.json()

def to_legacy_status(data: dict) -> dict:
    '''Flatten the raw GraphQL response into a simple status dict (text, counts, media, user)'''
    result = (data.get('data') or {}).get('tweetResult', {}).get('result') or {}
    if result.get('__typename') == 'TweetWithVisibilityResults':
        result = result.get('tweet') or {}
    status = result.get('legacy') or {}
    user = (((result.get('core') or {}).get('user_results') or {}).get('result') or {}).get('legacy') or {}
    status['user'] = user
    return status

def get_tweet_status(tweet_id: str):
    '''Fetch and flatten a tweet's status by ID. Returns None on any failure.'''
    try:
        session = requests.Session()
        guest_token = get_guest_token(session)
        raw = fetch_raw_tweet(session, tweet_id, guest_token)
        status = to_legacy_status(raw)
        return status if status else None
    except requests.exceptions.RequestException:
        return None

def download_media_item(session: requests.Session, file_path: str, media: dict) -> bool:
    '''Download a single media entry (photo/video/animated_gif) to file_path. Returns success.'''
    media_type = media.get('type')
    if media_type == 'photo':
        media_url = media.get('media_url_https') + '?name=orig'
    elif media_type in ('video', 'animated_gif'):
        variants = media.get('video_info', {}).get('variants', [])
        mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']
        if not mp4_variants:
            return False
        media_url = max(mp4_variants, key=lambda v: v.get('bitrate', 0))['url']
    else:
        return False
    try:
        response = session.get(media_url)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return False
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <twitter/x post url>")
        sys.exit(1)
    tweet_id = extract_tweet_id(sys.argv[1])
    status = get_tweet_status(tweet_id)
    print(status)
