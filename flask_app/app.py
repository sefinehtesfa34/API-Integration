import os 
import json
import requests
from datetime import datetime
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.background import BackgroundScheduler
from flask_app.populate import populate_profile, populate_casts
from flask_app.schema import BaseProfile, Casts, app, db
    
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
                print("Error fetching casts for FID {}".format(fid + 1))
        except Exception as e:
            db.session.rollback()
            print("Error fetching casts for FID {}: {}".format(fid + 1, str(e)))

                            
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
            response = get_response(fid + 1)
            if response.status_code == 200:
                user_data = response.json()['result']['user']
                new_profile = NewProfile.query.filter_by(fid=user_data['fid']).first()
                if not new_profile:
                    new_profile = NewProfile(fid=user_data['fid'])
                    db.session.add(new_profile)
                populate_profile(new_profile, user_data)
                db.session.commit()
                fetch_and_populate_casts(fid + 1, 100) # Populate casts for the user.
                print('Item with FID {} is populated in new profile!'.format(fid + 1))
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database operation failed: {e}")
        finally:
            db.session.close()

def fetch_and_update_all_profiles():
    with app.app_context():
        try:
            max_fid = get_max_fid()
            for fid in range(1, max_fid + 1): 
                response = requests.get(f'https://api.warpcast.com/v2/user?fid={fid}')
                if response.status_code == 200:
                    user_data = response.json()['result']['user']
                    profile = AllProfile.query.filter_by(fid=user_data['fid']).first()
                    if not profile:
                        profile = AllProfile(fid=user_data['fid'])  # Create a new profile instance
                        db.session.add(profile)

                    populate_profile(profile, user_data)  # Populate fields
                    db.session.commit()
                    print('Item with {} is populated in all profile!'.format(fid))
                else:
                    print(f"Failed to fetch profile for fid {fid}. Status code: {response.status_code}")
        except:
            db.session.rollback()
            print("Error fetching profiles")
        

    
scheduler = BackgroundScheduler()
scheduler.add_job(func= lambda: fetch_and_update_all_profiles(), trigger='interval', hours=24*7)
scheduler.add_job(func = lambda: fetch_and_update_user(app), trigger='interval', seconds=60)
scheduler.start()

@app.route('/')
def main():
    return "User profile updater is running!"

@app.route('/follow', methods=['POST'])
def follow():
    headers = {
        "Authorization": "Bearer MK-s1EcIl87La9zaBBWPdrZ9bPzxWcDCWDB5CMJTJR2Qm19zVpxg91drvCYkelvFIEhY9//fXS0ozkA3qgL0W4fsQ==",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    url = "https://client.warpcast.com/v2/follows"
    
    params = request.get_json()
    follower_id = params.get('follower_id')
    user_id = params.get('user_id')
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