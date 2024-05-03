import json
import logging
import requests
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.background import BackgroundScheduler
from .populate import populate_profile, populate_casts
from .schema import BaseProfile, Casts, app, db
import time
# File based logging

# logging.basicConfig(level=logging.DEBUG,
#                     filename='app.log',
#                     filemode='a',  # Append mode
#                     format='%(asctime)s - %(levelname)s - %(message)s',
#                     datefmt='%d-%b-%y %H:%M:%S')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

    
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
scheduler.add_job(func = lambda: fetch_and_update_user(app), trigger='interval', seconds=60)
scheduler.add_job(func = lambda: fetch_send_follow_request(user_id=506144), trigger='interval', seconds=60)
scheduler.start()

@app.route('/')
def main():
    return "User profile updater is running!"

if __name__ == '__main__':
    app.run(debug=True)