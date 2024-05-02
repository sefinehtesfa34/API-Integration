from datetime import datetime


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

