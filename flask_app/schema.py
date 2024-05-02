from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
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
