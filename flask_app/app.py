import json
import logging
import requests
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.background import BackgroundScheduler
from flask import render_template
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Sql2844@localhost/profile'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# File based logging

# logging.basicConfig(level=logging.DEBUG,
#                     filename='app.log',
#                     filemode='a',  # Append mode
#                     format='%(asctime)s - %(levelname)s - %(message)s',
#                     datefmt='%d-%b-%y %H:%M:%S')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

class BaseProfile(db.Model):
    __abstract__ = True  # This makes it so this class is not used to create any table
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    display_name = db.Column(db.String(255))
    pfp_url = db.Column(db.String(1024))
    pfp_verified = db.Column(db.Boolean)
    bio_text = db.Column(db.Text)
    location_place_id = db.Column(db.String(255))
    location_description = db.Column(db.String(255))
    follower_count = db.Column(db.Integer)
    following_count = db.Column(db.Integer)
    active_on_fc_network = db.Column(db.Boolean)
    viewer_context_following = db.Column(db.Boolean)
    viewer_context_followed_by = db.Column(db.Boolean)
    viewer_context_can_send_direct_casts = db.Column(db.Boolean)
    viewer_context_enable_notifications = db.Column(db.Boolean)
    viewer_context_has_uploaded_inbox_keys = db.Column(db.Boolean)
    extras_custody_address = db.Column(db.String(255))
    is_followed = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime, default=datetime.now())
    date_updated = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    
class Casts(db.Model):
    __tablename__ = 'casts'
    id = db.Column(db.Integer, primary_key=True)
    casts_hash = db.Column(db.String(255))
    thread_hash = db.Column(db.String(255))
    parent_source_type = db.Column(db.String(255))
    parent_source_url = db.Column(db.String(1024))
    author_fid = db.Column(db.BigInteger)
    author_username = db.Column(db.String(255))
    author_display_name = db.Column(db.String(255))
    author_pfp_url = db.Column(db.String(1024))
    author_pfp_verified = db.Column(db.Boolean)
    author_profile_bio = db.Column(db.Text)
    author_profile_location_description = db.Column(db.Text)
    author_follower_count = db.Column(db.Integer)
    author_following_count = db.Column(db.Integer)
    author_active_on_fc_network = db.Column(db.Boolean)
    message_text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    replies_count = db.Column(db.Integer)
    reactions_count = db.Column(db.Integer)
    recasts_count = db.Column(db.Integer)
    watches_count = db.Column(db.Integer)
    quote_count = db.Column(db.Integer) 
    combined_recast_count = db.Column(db.Integer)

class AllProfile(BaseProfile):
    __tablename__ = 'all_profiles'
    fid = db.Column(db.BigInteger, unique = False, nullable=False)

class NewProfile(BaseProfile):
    __tablename__ = 'new_profiles'
    fid = db.Column(db.BigInteger, unique = True, nullable=False)

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
    
with app.app_context():
    db.create_all()

def fetch_and_populate_casts(fid, limit):
    with app.app_context():
        try:
            logging.info(f"Fetching casts for FID {fid} with limit {limit}")
            response = requests.get(f"https://client.warpcast.com/v2/casts?fid={fid}&limit={limit}")
            if response.status_code == 200:
                casts_data = response.json()['result']['casts']
                for cast_data in casts_data:
                    cast = Casts(casts_hash=cast_data['hash'])
                    db.session.add(cast)
                    populate_casts(cast, cast_data)
                db.session.commit()
                logging.info(f"Successfully populated casts for FID {fid}")
            else:
                logging.error(f"Error fetching casts for FID {fid}: HTTP {response.status_code}")
        except Exception as e:
            db.session.rollback()
            logging.exception(f"Exception occurred while fetching casts for FID {fid}: {str(e)}")
                           
def get_max_fid():
    max_fid = db.session.query(db.func.max(AllProfile.fid)).scalar()
    return max_fid if max_fid else 508808

def get_response(fid):
    api_url = f'https://api.warpcast.com/v2/user?fid={fid}'
    response = requests.get(api_url)
    return response 

def fetch_and_update_user(app):
    with app.app_context():
        try:
            fid = db.session.query(db.func.max(NewProfile.fid)).scalar() or 0
            logging.info(f"Updating new user profile starting from FID {fid + 1}")
            response = get_response(fid + 1)
            if response.status_code == 200:
                user_data = response.json()['result']['user']
                new_profile = NewProfile.query.filter_by(fid=user_data['fid']).first()
                if not new_profile:
                    new_profile = NewProfile(fid=user_data['fid'])
                    db.session.add(new_profile)
                populate_profile(new_profile, user_data)
                db.session.commit()
                fetch_and_populate_casts(fid + 1, 100)
                logging.info(f"New user profile updated for FID {fid + 1}")
            else:
                logging.error(f"Failed to update user profile for FID {fid + 1}: HTTP {response.status_code}")
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.exception(f"Database operation failed for FID {fid + 1}: {e}")
        finally:
            db.session.close()


def fetch_and_update_all_profiles():
    with app.app_context():
        try:
            max_fid = get_max_fid()
            logging.info(f"Updating all profiles up to FID {max_fid}")
            for fid in range(1, max_fid + 1):
                response = requests.get(f'https://api.warpcast.com/v2/user?fid={fid}')
                if response.status_code == 200:
                    user_data = response.json()['result']['user']
                    profile = AllProfile.query.filter_by(fid=user_data['fid']).first()
                    if not profile:
                        profile = AllProfile(fid=user_data['fid'])
                        db.session.add(profile)
                    populate_profile(profile, user_data)
                    db.session.commit()
                else:
                    logging.warning(f"Failed to fetch profile for fid {fid}: HTTP {response.status_code}")
        except Exception as e:
            db.session.rollback()
            logging.exception("Error occurred during profile update: {}".format(str(e)))

def fetch_send_follow_request(user_id):
    with app.app_context():
        try:
            # user_id = 506144
            unfollowed_new_users = NewProfile.query.filter_by(is_followed = False).limit(100)
            for unfollowed_new_user in unfollowed_new_users:
                logging.info(f"Sending follow request to user {unfollowed_new_user.fid}")
                # Set up headers and the target URL
                headers = {
                    "Authorization": "Bearer MK-s1EcIl87La9zaBBWPdrZ9bPzxWcDCWDB5CMJTJR2Qm19zVpxg91drvCYkelvFIEhY9//fXS0ozkA3qgL0W4fsQ==",
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/000000000 Safari/537.36"
                }
                url = "https://client.warpcast.com/v2/follows"
                data = {
                    "targetFid": "{}".format(unfollowed_new_user.fid),
                    "e": json.dumps([{
                        "user_id": "{}".format(user_id)
                    }])
                }
                # Sending the PUT request to the follow API
                response = requests.put(url, json=data, headers=headers)
                # Handle response from the follow API
                if response.status_code == 200:
                    # Update the is_followed attribute of the profile to True
                    unfollowed_new_user.is_followed = True
                    db.session.commit()
                    logging.info(f"Follow request sent to user {unfollowed_new_user.fid}")
                else:
                    logging.error(f"Failed to send follow request to user {unfollowed_new_user.fid}: HTTP {response.status_code}")
                    db.session.rollback()
        except Exception as e:
            logging.exception(f"Error occurred while sending follow requests: {str(e)}")
            db.session.rollback()
        
    
scheduler = BackgroundScheduler()
scheduler.add_job(func= lambda: fetch_and_update_all_profiles(), trigger='interval', hours = 24*7)
scheduler.add_job(func = lambda: fetch_and_update_user(app), trigger='interval', hours = 6)
scheduler.add_job(func = lambda: fetch_send_follow_request(user_id=506144), trigger='interval', hours = 3)
scheduler.start()

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/recent-users')
def recent_users():
    recent_users = NewProfile.query.order_by(NewProfile.date_added.desc()).limit(10).all()
    return render_template('recent_users.html', users=recent_users)

@app.route('/top-followers')
def top_followers():
    users_by_followers = AllProfile.query.order_by(AllProfile.follower_count.desc()).limit(10).all()
    return render_template('top_followers.html', users=users_by_followers)

@app.route('/top-following')
def top_following():
    users_by_following = AllProfile.query.order_by(AllProfile.following_count.desc()).limit(10).all()
    return render_template('top_following.html', users=users_by_following)

@app.route('/messages')
def top_followers_messages():
    # Fetch messages from the database, excluding empty ones, and join with AllProfile to access follower counts
    # Sort them by the follower count of their authors in descending order and limit to top 10
    top_messages = db.session.query(Casts).limit(30).all()

    return render_template('top_followers_messages.html', messages=top_messages)


if __name__ == '__main__':
    app.run(debug=True)