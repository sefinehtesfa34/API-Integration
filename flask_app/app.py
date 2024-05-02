import os 
import json
import requests
from datetime import datetime
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.background import BackgroundScheduler
from flask_app.populate import populate_profile
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Sql2844@localhost/profile'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

def convert_milliseconds_to_datetime(ms):
    """Convert milliseconds since epoch to a datetime object."""
    return datetime(1970, 1, 1) + timedelta(milliseconds=ms)

def populate_casts(cast, cast_data):
    cast.casts_hash = cast_data.get('hash')
    cast.thread_hash = cast_data.get('threadHash')
    cast.parent_source_type = cast_data.get('parentSource', {}).get('type')
    cast.parent_source_url = cast_data.get('parentSource', {}).get('url')
    cast.author_fid = cast_data.get('author', {}).get('fid')
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
    
    
class AllProfile(BaseProfile):
    __tablename__ = 'all_profiles'
    fid = db.Column(db.BigInteger, unique = False, nullable=False)

class NewProfile(BaseProfile):
    __tablename__ = 'new_profiles'
    fid = db.Column(db.BigInteger, unique = True, nullable=False)

with app.app_context():
    db.create_all()

def fetch_and_populate_casts(fid, limit):
    with app.app_context():
        try:
            response = requests.get("https://client.warpcast.com/v2/casts?fid={}&limit={}".format(fid, limit))
            if response.status_code == 200:
                casts_data = response.json()['result']['casts']
                for cast_data in casts_data:
                    cast = Casts(casts_hash=cast_data['hash'])
                    db.session.add(cast)
                    populate_casts(cast, cast_data)
                    print("Cast with hash {} is populated!".format(cast_data['hash']))
                db.session.commit()  # Commit after all casts have been processed
            else:
                print("Error fetching casts for FID {}".format(fid))
        except Exception as e:
            db.session.rollback()
            print("Error fetching casts for FID {}: {}".format(fid, str(e)))

                            
def get_max_fid():
    max_fid = db.session.query(db.func.max(AllProfile.fid)).scalar()
    return max_fid if max_fid else 0

def get_response(fid):
    api_url = f'https://api.warpcast.com/v2/user?fid={fid}'
    response = requests.get(api_url)
    return response 

def fetch_and_update_user(app):
    with app.app_context():
        try:
            fid = db.session.query(db.func.max(NewProfile.fid)).scalar() or 0
            response = get_response(fid + 1)
            if response.status_code == 200:
                user_data = response.json()['result']['user']
                profile = NewProfile.query.filter_by(fid=user_data['fid']).first()
                if not profile:
                    profile = NewProfile(fid=user_data['fid'])
                    db.session.add(profile)
                populate_profile(profile, user_data)
                fetch_and_populate_casts(fid, 100) # Populate casts for the user.
                db.session.commit()
                print('Item with FID {} is populated!'.format(fid))
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database operation failed: {e}")
        finally:
            db.session.close()

def fetch_and_update_all_profiles():
    with app.app_context():
        try:
            max_fid = get_max_fid()
            for fid in range(max_fid + 1): 
                response = requests.get(f'https://api.warpcast.com/v2/user?fid={fid}')
                if response.status_code == 200:
                    user_data = response.json()['result']['user']
                    profile = AllProfile.query.filter_by(fid=user_data['fid']).first()
                    if not profile:
                        profile = AllProfile(fid=user_data['fid'])  # Create a new profile instance
                        db.session.add(profile)

                    populate_profile(profile, user_data)  # Populate fields
                    db.session.commit()
                    print('Item with {} is populated!'.format(fid))
                else:
                    print(f"Failed to fetch profile for fid {fid}. Status code: {response.status_code}")
        except:
            db.session.rollback()
            print("Error fetching profiles")
        

    
scheduler = BackgroundScheduler()
scheduler.add_job(func= lambda: fetch_and_update_all_profiles(), trigger='interval', seconds=60)
scheduler.add_job(func = lambda: fetch_and_update_user(app), trigger='interval', seconds=20)
scheduler.start()

@app.route('/')
def main():
    return "User profile updater is running!"

@app.route('/follow/<int:follower_id>/<int:user_id>', methods=['POST'])
def follow(follower_id, user_id):
    headers = {
        "Authorization": "Bearer MK-s1EcIl87La9zaBBWPdrZ9bPzxWcDCWDB5CMJTJR2Qm19zVpxg91drvCYkelvFIEhY9//fXS0ozkA3qgL0W4fsQ==",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    url = "https://client.warpcast.com/v2/follows"
    data = {
        "targetFid": "{}".format(user_id),
        "e": json.dumps([{
            "user_id": "{}".format(follower_id)
        }])
    }
    response = requests.put(url, json=data, headers=headers)
    if response.status_code == 200:
        return jsonify({'status': 'success', 'message': 'Follow request sent successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send follow request'}), 400

if __name__ == '__main__':
    app.run(debug=True)