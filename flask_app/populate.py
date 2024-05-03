from datetime import datetime, timedelta
def populate_profile(profile, user_data):
    # Helper function to populate a profile with data from a dictionary
    profile.username = user_data.get('username')
    profile.display_name = user_data.get('displayName')
    profile.pfp_url = user_data.get('pfp', {}).get('url')
    profile.pfp_verified = user_data.get('pfp', {}).get('verified', False)
    profile.bio_text = user_data.get('profile', {}).get('bio', {}).get('text', '')
    profile.location_place_id = user_data.get('profile', {}).get('location', {}).get('placeId', '')
    profile.location_description = user_data.get('profile', {}).get('location', {}).get('description', '')
    profile.follower_count = user_data.get('followerCount', 0)
    profile.following_count = user_data.get('followingCount', 0)
    profile.active_on_fc_network = user_data.get('activeOnFcNetwork', False)
    profile.viewer_context_following = user_data.get('viewerContext', {}).get('following', False)
    profile.viewer_context_followed_by = user_data.get('viewerContext', {}).get('followedBy', False)
    profile.viewer_context_can_send_direct_casts = user_data.get('viewerContext', {}).get('canSendDirectCasts', False)
    profile.viewer_context_enable_notifications = user_data.get('viewerContext', {}).get('enableNotifications', False)
    profile.viewer_context_has_uploaded_inbox_keys = user_data.get('viewerContext', {}).get('hasUploadedInboxKeys', False)
    profile.extras_custody_address = user_data.get('extras', {}).get('custodyAddress', '')
    profile.date_added = user_data.get('dateAdded', datetime.now())
    profile.date_updated = user_data.get('dateUpdated', datetime.now())
    profile.is_followed = False
    return profile

def convert_milliseconds_to_datetime(ms):
    """Convert milliseconds since epoch to a datetime object."""
    return datetime(1970, 1, 1) + timedelta(milliseconds=ms)

def populate_casts(cast, cast_data):
    cast.casts_hash = cast_data.get('hash')
    cast.thread_hash = cast_data.get('threadHash')
    cast.parent_source_type = cast_data.get('parentSource', {}).get('type')
    cast.parent_source_url = cast_data.get('parentSource', {}).get('url')
    cast.fid = cast_data.get('author', {}).get('fid')
    cast.author_username = cast_data.get('author', {}).get('username')
    cast.author_display_name = cast_data.get('author', {}).get('displayName')
    cast.author_pfp_url = cast_data.get('author', {}).get('pfp', {}).get('url')
    cast.author_pfp_verified = cast_data.get('author', {}).get('pfp', {}).get('verified', False)
    cast.author_profile_bio = cast_data.get('author', {}).get('profile', {}).get('bio', {}).get('text', '')
    cast.author_profile_location_description = cast_data.get('author', {}).get('profile', {}).get('location', {}).get('description', '')
    cast.author_follower_count = cast_data.get('author', {}).get('followerCount', 0)
    cast.author_following_count = cast_data.get('author', {}).get('followingCount', 0)
    cast.author_active_on_fc_network = cast_data.get('author', {}).get('activeOnFcNetwork', False)
    cast.message_text = cast_data.get('text', '')
    
    # Convert timestamp
    timestamp_ms = cast_data.get('timestamp')
    if timestamp_ms is not None:
        cast.timestamp = convert_milliseconds_to_datetime(timestamp_ms)
    else:
        cast.timestamp = datetime.now()  # or use default, if appropriate

    cast.replies_count = cast_data.get('replies', {}).get('count', 0)
    cast.reactions_count = cast_data.get('reactions', {}).get('count', 0)
    cast.recasts_count = cast_data.get('recasts', {}).get('count', 0)
    cast.watches_count = cast_data.get('watches', {}).get('count', 0)
    cast.quote_count = cast_data.get('quoteCount', 0)
    cast.combined_recast_count = cast_data.get('combinedRecastCount', 0)
    