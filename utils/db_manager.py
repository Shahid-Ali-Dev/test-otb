from models import db, User, PortfolioItem, ContactSubmission, UserReview
from utils.auth import hash_password, check_password
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename

class DatabaseManager:
    def __init__(self):
        pass
    # User Methods
    def get_user_by_id(self, user_id):
        return User.query.get(user_id)

    def get_user_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def create_user(self, user_data):
        try:
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                password=user_data['password'],
                role=user_data.get('role', 'user'),
                provider=user_data.get('provider', 'email')
            )
            db.session.add(user)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {str(e)}")
            return False

    def update_user_profile(self, user_id, name, occupation, profile_picture_url=None):
        try:
            user = User.query.get(user_id)
            if user:
                user.name = name
                user.occupation = occupation
                if profile_picture_url:
                    user.profile_picture = profile_picture_url  # Store Cloudinary URL
                user.updated_at = datetime.utcnow()
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error updating user profile: {str(e)}")
            return False

    def update_last_login(self, user_id):
        user = User.query.get(user_id)
        if user:
            user.last_login = datetime.utcnow()
            db.session.commit()

    # Portfolio Methods (keep existing)
    def get_portfolio_items(self):
        """Get all portfolio items ordered by: videos first, then coming soon, latest first"""
        try:
            # Get all items ordered by status (active first) and then by creation date (latest first)
            items = PortfolioItem.query.order_by(
                db.case(
                    (PortfolioItem.status == 'active', 0),
                    (PortfolioItem.status == 'coming_soon', 1),
                    else_=2
                ),
                PortfolioItem.created_at.desc()
            ).all()
            return items
        except Exception as e:
            print(f"Error getting portfolio items: {str(e)}")
            return []

    def save_portfolio_item(self, item_data):
        """Save portfolio item to database"""
        try:
            # Convert tags list to JSON string
            tags_json = json.dumps(item_data.get('tags', []))
            
            item = PortfolioItem(
                title=item_data['title'],
                description=item_data['description'],
                youtube_id=item_data.get('youtube_id'),
                video_type=item_data.get('video_type'),
                category=item_data['category'],
                tags=tags_json,
                status=item_data.get('status', 'active')
            )
            db.session.add(item)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error saving portfolio item: {str(e)}")
            return False

    def delete_portfolio_item(self, item_id):
        """Delete portfolio item from database"""
        try:
            item = PortfolioItem.query.get(item_id)
            if item:
                db.session.delete(item)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting portfolio item: {str(e)}")
            return False

    def get_portfolio_stats(self):
        """Get portfolio statistics for admin dashboard"""
        try:
            total_items = PortfolioItem.query.count()
            active_count = PortfolioItem.query.filter_by(status='active').count()
            coming_soon_count = PortfolioItem.query.filter_by(status='coming_soon').count()
            youtube_count = PortfolioItem.query.filter(
                PortfolioItem.video_type == 'youtube',
                PortfolioItem.status == 'active'
            ).count()
            instagram_count = PortfolioItem.query.filter(
                PortfolioItem.video_type == 'instagram', 
                PortfolioItem.status == 'active'
            ).count()
            
            return {
                'total': total_items,
                'active': active_count,
                'coming_soon': coming_soon_count,
                'youtube': youtube_count,
                'instagram': instagram_count
            }
        except Exception as e:
            print(f"Error getting portfolio stats: {str(e)}")
            return {}

    # Contact Methods (keep existing)
    def save_contact_submission(self, contact_data):
        try:
            submission = ContactSubmission(
                name=contact_data['name'],
                email=contact_data['email'],
                company=contact_data.get('company', ''),
                phone=contact_data.get('phone', ''),
                service=contact_data.get('service', ''),
                budget=contact_data.get('budget', ''),
                message=contact_data.get('message', '')
            )
            db.session.add(submission)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error saving contact submission: {str(e)}")
            return False
        
    def get_user_reviews(self, approved_only=True, limit=None):
        """Get user-submitted reviews"""
        try:
            query = UserReview.query
            
            if approved_only:
                query = query.filter_by(is_approved=True)
                
            if limit:
                query = query.limit(limit)
                
            return query.order_by(UserReview.created_at.desc()).all()
        except Exception as e:
            print(f"Error getting user reviews: {str(e)}")
            return []

    def create_user_review(self, user_id, rating, comment, service_category=None):
        """Create a new user review"""
        try:
            review = UserReview(
                user_id=user_id,
                rating=rating,
                comment=comment,
                service_category=service_category
            )
            db.session.add(review)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error creating user review: {str(e)}")
            db.session.rollback()
            return False
        
    def get_user_by_google_id(self, google_id):
        """Get user by Google ID"""
        try:
            return User.query.filter_by(google_id=google_id).first()
        except Exception as e:
            print(f"Error getting user by Google ID: {str(e)}")
            return None
    
    def create_google_user(self, user_data):
        """Create a new user with Google OAuth"""
        try:
            user = User(
                email=user_data['email'],
                name=user_data['name'],
                google_id=user_data['google_id'],
                provider='google',
                profile_picture=user_data.get('profile_picture'),
                password='',  # ✅ Set empty string instead of None
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            print(f"Error creating Google user: {str(e)}")
            return None
    
    def update_user_from_google(self, user, user_data):
        """Update existing user with Google data (if needed)"""
        try:
            # Only update name and profile picture if they're not set
            if not user.name or user.name == 'User':
                user.name = user_data['name']
            
            if not user.profile_picture and user_data.get('profile_picture'):
                user.profile_picture = user_data['profile_picture']
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            print(f"Error updating user from Google: {str(e)}")
            return None
