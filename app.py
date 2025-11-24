from venv import logger
import re
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, send_from_directory
from forms import ProfileForm 
from utils.auth import hash_password, check_password
from ai_analytics.youtube_analyzer import YouTubeAnalyzer
from ai_analytics.instagram_analyzer import InstagramAnalyzer
import traceback
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import requests
from utils.cloudinary_manager import CloudinaryManager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
from flask_compress import Compress
# Import new database modules and service data
from models import db, User as UserModel, UserReview, PortfolioItem, ContactSubmission
from utils.db_manager import DatabaseManager
from data.service_data import SERVICE_DATA, SERVICE_VIDEOS, DEFAULT_SERVICE_VIDEO
from data.portfolio_data import portfolio_data
from sqlalchemy import text

# ✅ LOAD ENVIRONMENT VARIABLES FIRST
load_dotenv()

# ✅ NOW CREATE THE APP WITH DIRECT ENVIRONMENT VARIABLES
app = Flask(__name__)

# Flask Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'demo-secret-key-123')

# ✅ LOAD ENVIRONMENT VARIABLES FIRST
load_dotenv()

# ✅ NOW CREATE THE APP WITH DIRECT ENVIRONMENT VARIABLES
app = Flask(__name__)

# Flask Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'demo-secret-key-123')

# Database Configuration - Enhanced for Neon
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Ensure it starts with postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,  # 5 minutes
        'pool_size': 5,       # Reduced for Neon
        'max_overflow': 10,   # Reduced for Neon
        'pool_timeout': 30,
    }
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local.db'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool
    }
# Store other config values directly in app.config or use os.environ.get() when needed
app.config['CLOUDINARY_CLOUD_NAME'] = os.environ.get('CLOUDINARY_CLOUD_NAME')
app.config['CLOUDINARY_API_KEY'] = os.environ.get('CLOUDINARY_API_KEY')
app.config['CLOUDINARY_API_SECRET'] = os.environ.get('CLOUDINARY_API_SECRET')
app.config['BREVO_SMTP_USER'] = os.environ.get('BREVO_SMTP_USER')
app.config['BREVO_SMTP_PASSWORD'] = os.environ.get('BREVO_SMTP_PASSWORD')
app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'

compress = Compress()
compress.init_app(app)

# Add configuration for file uploads
app.config['UPLOAD_FOLDER'] = 'static/uploads/profile_pictures'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# If using SQLite, add these configurations
if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    from sqlalchemy.pool import StaticPool
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'check_same_thread': False,
            'timeout': 30
        },
        'poolclass': StaticPool
    }

# Initialize Database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Initialize Database Manager 
db_manager = DatabaseManager()

# User class for Flask-Login (UPDATED)
class User(UserMixin):
    def __init__(self, user_model):
        self.id = user_model.id
        self.email = user_model.email
        self.name = user_model.name
        self.occupation = user_model.occupation
        self.profile_picture = user_model.profile_picture
        self.role = user_model.role
        self.provider = user_model.provider
        self.created_at = user_model.created_at  
        self.last_login = user_model.last_login 

# Add this after your imports in app.py
@app.template_filter('format_number')
def format_number_filter(num):
    """Format numbers with K/M suffixes"""
    if not num:
        return '0'
    
    try:
        num = int(num)
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return str(num)
    except (ValueError, TypeError):
        return str(num)

@login_manager.user_loader
def load_user(user_id):
    # Use the INSTANCE db_manager
    user_data = db_manager.get_user_by_id(user_id)
    if user_data:
        return User(user_data)
    return None

# Forms (keep all your existing forms the same)
class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class PortfolioItemForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    youtube_id = StringField('YouTube Video ID', validators=[Optional(), Length(max=20)])
    category = SelectField('Category', choices=[
        ('creative', 'Creative & Content'),
        ('social', 'Social Growth'),
        ('marketing', 'Performance Marketing'),
        ('development', 'Web Development'),
        ('ai', 'AI Solutions')
    ], validators=[DataRequired()])
    tags = StringField('Tags (comma separated)', validators=[Optional()])
    is_coming_soon = BooleanField('Mark as Coming Soon')
    submit = SubmitField('Save Project')

# Portfolio management functions (UPDATED)
def get_portfolio_items():
    """Get portfolio items from database with proper ordering"""
    try:
        # Use the INSTANCE db_manager
        items = db_manager.get_portfolio_items()
        if items is None:
            return []
        
        # Convert SQLAlchemy objects to dictionaries for templates
        portfolio_data = []
        for item in items:
            # Handle potential None values
            tags = []
            if item.tags:
                try:
                    tags = json.loads(item.tags) if isinstance(item.tags, str) else item.tags
                except json.JSONDecodeError:
                    tags = item.tags if isinstance(item.tags, list) else []
            
            portfolio_data.append({
                'id': item.id,
                'title': item.title or 'Untitled',
                'description': item.description or '',
                'youtube_id': item.youtube_id,
                'videoType': item.video_type,  # Map to match frontend expectation
                'category': item.category or 'creative',
                'tags': tags,
                'status': item.status or 'active',
                'created_at': item.created_at or datetime.utcnow()
            })
        
        print(f"get_portfolio_items: returning {len(portfolio_data)} items")
        return portfolio_data
    except Exception as e:
        print(f"Error getting portfolio items: {str(e)}")
        traceback.print_exc()
        return []
    
def save_portfolio_item(item_data):
    """Save portfolio item to PostgreSQL database"""
    try:
        # Use the INSTANCE db_manager
        return db_manager.save_portfolio_item(item_data)
    except Exception as e:
        print(f"Error saving portfolio item: {str(e)}")
        return False

def delete_portfolio_item(item_id):
    """Delete portfolio item from PostgreSQL database"""
    try:
        # Use the INSTANCE db_manager
        return db_manager.delete_portfolio_item(item_id)
    except Exception as e:
        print(f"Error deleting portfolio item: {str(e)}")
        return False

# Routes (keep all your existing routes the same)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services')
def services():
    return render_template('services.html')

# Profile route with Cloudinary integration
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    # Pre-populate form with current user data
    if request.method == 'GET':
        form.name.data = current_user.name
        form.occupation.data = current_user.occupation
    
    if form.validate_on_submit():
        try:
            profile_picture_url = None
            
            # Handle file upload
            if form.profile_picture.data:
                file = form.profile_picture.data
                
                # Check file size
                if file.content_length > 5 * 1024 * 1024:
                    flash('File size must be less than 5MB.', 'danger')
                    return render_template('auth/profile.html', form=form)
                
                # Check file type
                allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
                if file.content_type not in allowed_types:
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, or GIF.', 'danger')
                    return render_template('auth/profile.html', form=form)
                
                # Delete old profile picture from Cloudinary if exists
                if current_user.profile_picture and 'cloudinary.com' in current_user.profile_picture:
                    CloudinaryManager.delete_profile_picture(current_user.id)
                
                # Upload new profile picture to Cloudinary
                profile_picture_url = CloudinaryManager.upload_profile_picture(file, current_user.id)
                
                if not profile_picture_url:
                    flash('Error uploading image. Please try again.', 'danger')
                    return render_template('auth/profile.html', form=form)
            
            # Update user profile
            success = db_manager.update_user_profile(
                user_id=current_user.id,
                name=form.name.data,
                occupation=form.occupation.data,
                profile_picture_url=profile_picture_url
            )
            
            if success:
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Error updating profile. Please try again.', 'danger')
                
        except Exception as e:
            flash('An error occurred while updating your profile.', 'danger')
            print(f'Profile update error: {str(e)}')
    
    return render_template('auth/profile.html', form=form)

# In app.py - UPDATE the service_detail route
@app.route('/service/<service_id>')
def service_detail(service_id):
    service_data = SERVICE_DATA.get(service_id)
    if not service_data:
        flash('Service not found.', 'danger')
        return redirect(url_for('services'))
    
    # Get Cloudinary video URL
    video_url = SERVICE_VIDEOS.get(service_id)
    if not video_url:
        # Fallback to default video
        video_url = SERVICE_VIDEOS.get('default-service', DEFAULT_SERVICE_VIDEO)
    
    # Add video URL to service data for template
    service_data['video_url'] = video_url
    
    return render_template('service-detail.html', 
                         service_data=service_data)

@app.route('/youtube-analyzer')
def youtube_analyzer():
    """Public YouTube Analytics tool for everyone"""
    return render_template('youtube_analyzer.html')

@app.route('/api/analyze-youtube-channel', methods=['POST'])
def analyze_youtube_channel():
    """API endpoint for public YouTube channel analysis - DEBUG VERSION"""
    try:
        data = request.get_json()
        channel_identifier = data.get('channel_identifier', '').strip()
        
        if not channel_identifier:
            return jsonify({'success': False, 'message': 'Channel identifier is required'})
        
        logger.info(f"🎯 [API] Analyzing: {channel_identifier}")
        
        # Extract channel ID from URL if provided
        channel_id = extract_channel_id(channel_identifier)
        
        if not channel_id:
            return jsonify({'success': False, 'message': 'Invalid YouTube channel identifier'})
        
        logger.info(f"🔍 [API] Extracted identifier: {channel_id}")
        
        # Initialize analyzer
        youtube_analyzer = YouTubeAnalyzer(
            os.getenv('YOUTUBE_API_KEY'), 
            db,
            groq_api_key=os.getenv('GROQ_API_KEY')
        )
        
        # CRITICAL: If it's a custom URL, resolve it to actual channel ID FIRST
        if channel_id.startswith('@'):
            logger.info(f"🔄 [API] Resolving custom URL: {channel_id}")
            resolved_id = youtube_analyzer.resolve_custom_url_to_channel_id(channel_id, os.getenv('YOUTUBE_API_KEY'))
            if resolved_id:
                channel_id = resolved_id
                logger.info(f"✅ [API] Using resolved channel ID: {channel_id}")
            else:
                logger.error(f"❌ [API] Failed to resolve custom URL: {channel_id}")
                return jsonify({
                    'success': False, 
                    'message': 'Could not find channel. Please check the custom URL and try again.'
                })
        
        # Analyze the channel
        logger.info(f"🔍 [API] Starting analysis for channel ID: {channel_id}")
        analysis = youtube_analyzer.analyze_channel_public(channel_id, force_refresh=True)
        
        # Check if we got valid data
        if not analysis or analysis.get('data_source') == 'public_fallback':
            return jsonify({
                'success': False, 
                'message': 'Could not find channel data. Please check the channel URL/ID and try again.'
            })
        
        # Verify we have engagement data
        engagement_data = analysis.get('engagement_metrics', {})
        if engagement_data.get('avg_engagement_rate', 0) == 0 and engagement_data.get('total_recent_likes', 0) == 0:
            logger.warning(f"⚠️ [API] No engagement data found for channel: {channel_id}")
        
        logger.info(f"✅ [API] Analysis completed successfully for: {channel_id}")
        return jsonify({
            'success': True,
            'analysis': analysis,
            'channel_id': channel_id
        })
        
    except Exception as e:
        logger.error(f"❌ [API] Error analyzing YouTube channel: {str(e)}")
        import traceback
        logger.error(f"❌ [API] Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'message': f'Error analyzing channel: {str(e)}'
        })
    

def extract_channel_id(identifier):
    """Extract channel ID from various input formats with improved URL parsing"""
    if not identifier:
        return None
    
    identifier = identifier.strip()
    
    # If it's already a channel ID (starts with UC and 24 characters)
    if identifier.startswith('UC') and len(identifier) == 24:
        return identifier
    
    # Handle various YouTube URL formats
  
    
    # Pattern 1: youtube.com/channel/UC... (direct channel ID)
    channel_pattern = r'youtube\.com/channel/([a-zA-Z0-9_-]{24})'
    match = re.search(channel_pattern, identifier)
    if match:
        return match.group(1)
    
    # Pattern 2: youtube.com/@username (custom URL)
    custom_pattern = r'youtube\.com/@([a-zA-Z0-9_-]+)'
    match = re.search(custom_pattern, identifier)
    if match:
        return f"@{match.group(1)}"
    
    # Pattern 3: Handle URLs with query parameters like ?si=...
    # Remove query parameters and fragments for cleaner matching
    clean_identifier = re.sub(r'[?#].*$', '', identifier)
    if clean_identifier != identifier:
        # Recursively try with cleaned identifier
        return extract_channel_id(clean_identifier)
    
    # Pattern 4: Direct @username input (without youtube.com)
    if re.match(r'^@[a-zA-Z0-9_-]+$', identifier):
        return identifier
    
    # Pattern 5: Simple username (without @)
    if re.match(r'^[a-zA-Z0-9_-]+$', identifier) and not identifier.startswith('UC'):
        return f"@{identifier}"
    
    # If it's a URL but no pattern matched, return as-is for API to handle
    if 'youtube.com' in identifier or 'youtu.be' in identifier:
        return identifier
    
    # Return original identifier for the API to handle
    return identifier

@app.route('/portfolio')
def portfolio():
    portfolio_items = get_portfolio_items()
    # Convert to list of dictionaries for JSON serialization
    portfolio_data = []
    for item in portfolio_items:
        portfolio_data.append({
            'id': item['id'],
            'title': item['title'],
            'description': item['description'],
            'youtube_id': item.get('youtube_id'),
            'video_id': item.get('youtube_id'),  # Add both for compatibility
            'videoType': item.get('videoType'),
            'video_type': item.get('videoType'),  # Add both for compatibility
            'category': item['category'],
            'tags': item['tags'],
            'status': item['status']
        })
    
    print(f"Portfolio route: sending {len(portfolio_data)} items to template")
    return render_template('portfolio.html', portfolio_items=portfolio_data)

@app.route('/admin/portfolio')
@login_required
def admin_portfolio():
    try:
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('portfolio'))
        
        portfolio_items = get_portfolio_items()
        stats = db_manager.get_portfolio_stats()
        
        form = PortfolioItemForm()
        
        return render_template('admin/portfolio.html', 
                             portfolio_items=portfolio_items,
                             active_count=stats.get('active', 0),
                             coming_soon_count=stats.get('coming_soon', 0),
                             youtube_count=stats.get('youtube', 0),
                             instagram_count=stats.get('instagram', 0),
                             form=form)
                             
    except Exception as e:
        print(f"ERROR in admin_portfolio: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while loading the portfolio page.', 'danger')
        return redirect(url_for('index'))
    
@app.route('/admin/profile-analyzer')
@login_required
def profile_analyzer():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Test database connection first
        db.session.execute(text('SELECT 1'))
        
        # Initialize analyzers
        youtube_analyzer = YouTubeAnalyzer(
            os.getenv('YOUTUBE_API_KEY'), 
            db,
            groq_api_key=os.getenv('GROQ_API_KEY')
        )
        instagram_analyzer = InstagramAnalyzer(db)
        
        # Your channel IDs
        youtube_channel_id = "UCDFtESeQyC04kAe-zklSs3w"
        instagram_username = "shoutotb"
        
        # Get real YouTube data with connection safety
        youtube_analysis = youtube_analyzer.analyze_channel(youtube_channel_id, force_refresh=False)
        
        # 🔥 FLATTEN THE DATA STRUCTURE FOR FRONTEND
        youtube_data = youtube_analyzer.flatten_youtube_data(youtube_analysis)
        
        # Get Instagram data
        instagram_analysis = instagram_analyzer.analyze_profile(instagram_username)
        instagram_data = instagram_analysis
        
        return render_template('admin/profile_analyzer.html', 
                             youtube_data=youtube_data,
                             instagram_data=instagram_data,
                             youtube_channel_id=youtube_channel_id,
                             instagram_username=instagram_username)
                             
    except Exception as e:
        print(f"Error in profile_analyzer: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Check if it's a database connection error
        if "password authentication failed" in str(e) or "connection" in str(e).lower():
            flash('Database connection issue. Please try again in a moment.', 'danger')
        else:
            flash(f'Error loading analytics: {str(e)}', 'danger')
        
        # Provide fallback data
        fallback_data = {
            'channel_title': 'Temporarily Unavailable',
            'subscribers': 0,
            'total_views': 0,
            'total_videos': 0,
            'engagement_rate': 0,
            'channel_health': 0,
            'performance_tier': 'Connection Error',
            'optimal_video_length': 'Unknown',
            'performance_consistency': 0,
            'performance_trend': 'Unknown',
            'ai_insights': [],
            'content_analysis': {},
            'demographics': {},
            'data_source': 'error'
        }
        
        return render_template('admin/profile_analyzer.html', 
                             youtube_data=fallback_data, 
                             instagram_data={},
                             youtube_channel_id="UCDFtESeQyC04kAe-zklSs3w",
                             instagram_username="shoutotb")

def safe_db_operation(func):
    """Decorator to handle database connection issues"""
    def wrapper(*args, **kwargs):
        try:
            # Test connection first
            db.session.execute(text('SELECT 1'))
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            # Try to reconnect
            try:
                db.session.remove()
                db.session.execute(text('SELECT 1'))
                return func(*args, **kwargs)
            except:
                flash('Database temporarily unavailable. Please try again.', 'danger')
                return redirect(url_for('index'))
    return wrapper
    
@app.route('/admin/clear-cache', methods=['POST'])
@login_required
def clear_cache():
    """Clear cached analytics data"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        from models import YouTubeAnalyticsSnapshot
        from datetime import datetime
        
        # Delete all cached data for your channel
        deleted_count = YouTubeAnalyticsSnapshot.query.filter(
            YouTubeAnalyticsSnapshot.channel_id == "UCDFtESeQyC04kAe-zklSs3w"
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Cleared {deleted_count} cached records'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/test-db')
def test_db():
    """Test database connection and tables"""
    try:
        # Test connection with text() wrapper
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        
        # Test tables
        tables = {
            'users': User.query.count(),
            'portfolio_items': PortfolioItem.query.count(),
            'contact_submissions': ContactSubmission.query.count(),
            'user_reviews': UserReview.query.count()
        }
        
        return jsonify({
            'success': True,
            'message': 'Database is working!',
            'tables': tables
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Database error: {str(e)}'
        }), 500

        
@app.route('/admin/refresh-analytics', methods=['POST'])
@login_required
def refresh_analytics():
    """Refresh analytics data with connection safety"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        # Test database connection first
        db.session.execute(text('SELECT 1'))
        
        data = request.get_json()
        platform = data.get('platform')
        identifier = data.get('identifier')
        force_refresh = data.get('force_refresh', True)
        
        logger.info(f"Refreshing analytics for {platform}: {identifier}, force_refresh: {force_refresh}")
        
        if platform == 'youtube':
            analyzer = YouTubeAnalyzer(os.getenv('YOUTUBE_API_KEY'), db)
            analysis = analyzer.analyze_channel(identifier, force_refresh=force_refresh)
            
        elif platform == 'instagram':
            analyzer = InstagramAnalyzer(db)
            analysis = analyzer.analyze_profile(identifier, force_refresh)
            
        else:
            return jsonify({'success': False, 'message': 'Invalid platform'})
        
        return jsonify({
            'success': True,
            'message': 'Analytics refreshed successfully',
            'data': analysis,
            'data_source': analysis.get('data_source', 'unknown')
        })
        
    except Exception as e:
        logger.error(f"Error refreshing analytics: {str(e)}")
        
        # Specific error messages
        if "password authentication" in str(e):
            error_msg = "Database connection issue. Please check your Neon database credentials."
        elif "connection" in str(e).lower():
            error_msg = "Database connection lost. Please try again."
        else:
            error_msg = f'Error: {str(e)}'
            
        return jsonify({'success': False, 'message': error_msg})

@app.route('/admin/get-analytics/<platform>/<identifier>')
@login_required
def get_analytics(platform, identifier):
    """Get current analytics data"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'})
    
    try:
        if platform == 'youtube':
            analyzer = YouTubeAnalyzer(os.getenv('YOUTUBE_API_KEY'), db)
            analysis = analyzer.analyze_channel(identifier, force_refresh=False)
            
        elif platform == 'instagram':
            analyzer = InstagramAnalyzer(db)
            analysis = analyzer.analyze_profile(identifier, force_refresh=False)
            
        else:
            return jsonify({'error': 'Invalid platform'})
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/admin/portfolio/item/<int:item_id>')
@login_required
def get_portfolio_item(item_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        item = PortfolioItem.query.get_or_404(item_id)
        
        # Parse tags from JSON string
        tags = []
        if item.tags:
            try:
                tags = json.loads(item.tags) if isinstance(item.tags, str) else item.tags
            except json.JSONDecodeError:
                tags = item.tags if isinstance(item.tags, list) else []
        
        return jsonify({
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'youtube_id': item.youtube_id,
            'video_type': item.video_type,
            'category': item.category,
            'tags': tags,
            'status': item.status,
            'created_at': item.created_at.isoformat() if item.created_at else None
        })
    except Exception as e:
        print(f"Error getting portfolio item: {str(e)}")
        return jsonify({'error': 'Item not found'}), 404

@app.route('/admin/portfolio/add', methods=['POST'])
@login_required
def add_portfolio_item():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        data = request.get_json()
        
        # Create new portfolio item
        item = PortfolioItem(
            title=data['title'],
            description=data['description'],
            category=data['category'],
            tags=json.dumps(data.get('tags', [])),
            status=data.get('status', 'active'),
            youtube_id=data.get('youtube_id'),
            video_type=data.get('video_type'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(item)
        db.session.commit()
        
        flash('Portfolio item added successfully!', 'success')
        return jsonify({'success': True, 'message': 'Item added successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding portfolio item: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to add item'})

@app.route('/admin/portfolio/edit/<int:item_id>', methods=['PUT'])
@login_required
def edit_portfolio_item(item_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        data = request.get_json()
        
        # Get the existing item
        item = PortfolioItem.query.get_or_404(item_id)
        
        # Update fields
        item.title = data['title']
        item.description = data['description']
        item.category = data['category']
        item.tags = json.dumps(data.get('tags', []))
        item.status = data.get('status', 'active')
        item.youtube_id = data.get('youtube_id')
        item.video_type = data.get('video_type')
        item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Portfolio item updated successfully!', 'success')
        return jsonify({'success': True, 'message': 'Item updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating portfolio item: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to update item'})

@app.route('/admin/portfolio/delete/<int:item_id>', methods=['DELETE'])
@login_required
def delete_portfolio_item_route(item_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        item = PortfolioItem.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        
        flash('Portfolio item deleted successfully!', 'success')
        return jsonify({'success': True, 'message': 'Item deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting portfolio item: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to delete item'})
    
@app.route('/add_review', methods=['POST'])
@login_required
def add_review():
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        service_category = request.form.get('service_category')
        
        # Handle custom service category
        if service_category == 'other':
            service_category = request.form.get('service_category_other', '').strip()
        
        # Validate inputs
        if not rating or not comment:
            flash('Please provide both rating and comment.', 'danger')
            return redirect(url_for('index'))
        
        try:
            # Validate rating is a number between 1-5
            rating_int = int(rating)
            if rating_int < 1 or rating_int > 5:
                flash('Please provide a rating between 1 and 5.', 'danger')
                return redirect(url_for('index'))
            
            # Save review to database
            success = db_manager.create_user_review(
                user_id=current_user.id,
                rating=rating_int,
                comment=comment.strip(),
                service_category=service_category
            )
            
            if success:
                flash('Thank you for your review! It will be visible after approval.', 'success')
            else:
                flash('There was an error submitting your review. Please try again.', 'danger')
                
        except ValueError:
            flash('Please provide a valid rating number.', 'danger')
        except Exception as e:
            print(f"Error saving review: {str(e)}")
            flash('There was an error submitting your review. Please try again.', 'danger')
        
        return redirect(url_for('index'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    # Default form data (for GET requests or when no form data exists)
    form_data = {
        'name': '', 'email': '', 'company': '', 'phone': '',
        'service': '', 'service_other': '', 'budget': '', 'message': ''
    }
    
    if request.method == 'POST':
        try:
            data = request.form
            
            # Validate required fields
            if not data.get('name') or not data.get('email'):
                flash('Name and email are required.', 'danger')
                # Preserve form data on error
                form_data = {key: data.get(key, '') for key in form_data.keys()}
                return render_template('contact.html', form_data=form_data)
            
            # Handle service selection - check if "other" was selected
            service_value = data.get('service', '')
            if service_value == 'other':
                # Use the custom service input
                service_value = data.get('service_other', '').strip()
                if not service_value:
                    flash('Please specify the service you are interested in.', 'danger')
                    form_data = {key: data.get(key, '') for key in form_data.keys()}
                    return render_template('contact.html', form_data=form_data)
            
            # Save to database
            submission = ContactSubmission(
                name=data.get('name', ''),
                email=data.get('email', ''),
                company=data.get('company', ''),
                phone=data.get('phone', ''),
                service=service_value,  # Use the determined service value
                budget=data.get('budget', ''),
                message=data.get('message', ''),
                submitted_at=datetime.utcnow()
            )
            
            db.session.add(submission)
            db.session.commit()
            print(f"✅ Contact submission saved to database with ID: {submission.id}")
            
            # Send email via Brevo API
            brevo_api_key = os.environ.get('BREVO_API_KEY')
            
            if brevo_api_key:
                api_url = "https://api.brevo.com/v3/smtp/email"
                
                html_content = f"""
                <h3>📩 New Contact Form Submission - Shout OTB</h3>
                <p><strong>Name:</strong> {data.get('name', '')}</p>
                <p><strong>Email:</strong> {data.get('email', '')}</p>
                <p><strong>Company:</strong> {data.get('company', '')}</p>
                <p><strong>Phone:</strong> {data.get('phone', '')}</p>
                <p><strong>Service:</strong> {data.get('service', '')}</p>
                <p><strong>Budget:</strong> {data.get('budget', '')}</p>
                <p><strong>Message:</strong></p>
                <p>{data.get('message', '')}</p>
                <br>
                <p><em>Submission ID: {submission.id}</em></p>
                <p><em>Received at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</em></p>
                """
                
                payload = {
                    "sender": {
                        "name": "Shout OTB Website",
                        "email": "shoutotbot@gmail.com"
                    },
                    "to": [
                        {
                            "email": "shahid3332210@gmail.com",
                            "name": "Shahid"
                        }
                    ],
                    "subject": f"New Contact: {data.get('name', 'Visitor')}",
                    "htmlContent": html_content
                }
                
                headers = {
                    "accept": "application/json",
                    "content-type": "application/json",
                    "api-key": brevo_api_key
                }
                
                response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                
                if response.status_code == 201:
                    flash('🎉 Message sent successfully! We will get back to you soon.', 'success')
                else:
                    print(f"Brevo API error: {response.status_code} - {response.text}")
                    flash('📩 Message received! We saved your information but had trouble sending confirmation. We will contact you soon.', 'warning')
            else:
                flash('📩 Message received! We saved your information and will contact you soon.', 'success')
            
            # Clear form data on success
            form_data = {key: '' for key in form_data.keys()}
            return render_template('contact.html', form_data=form_data)
            
        except Exception as e:
            print(f"General error: {str(e)}")
            flash('❌ Server error. Please try again.', 'danger')
            # Preserve form data on error
            form_data = {key: request.form.get(key, '') for key in form_data.keys()}
            return render_template('contact.html', form_data=form_data)
    
    # GET request - render the contact page with empty form
    return render_template('contact.html', form_data=form_data)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Check if user already exists
            existing_user = db_manager.get_user_by_email(form.email.data)
            if existing_user:
                flash('Email already registered. Please login.', 'danger')
                return redirect(url_for('login'))
            
            # Hash password
            
            hashed_password = hash_password(form.password.data)
            
            # Create user data
            user_data = {
                'name': form.name.data,
                'email': form.email.data,
                'password': hashed_password,
                'provider': 'email',
                'role': 'user'
            }
            
            # Save to PostgreSQL
            success = db_manager.create_user(user_data)
            
            if success:
                # Get the created user and log them in
                user_data = db_manager.get_user_by_email(form.email.data)
                if user_data:
                    user = User(user_data)
                    login_user(user)
                    flash('Registration successful! Welcome to Shout OTB.', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Registration completed but login failed. Please try logging in.', 'warning')
                    return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'danger')
                
        except Exception as e:
            flash('An error occurred during registration. Please try again.', 'danger')
            print(f'Registration error: {str(e)}')
    
    return render_template('auth/register.html', form=form)

@app.route('/api/generate-analysis-pdf', methods=['POST'])
@login_required
def generate_analysis_pdf():
    """Generate PDF report for YouTube analysis"""
    try:
        print("=== PDF GENERATION DEBUG START ===")
        
        data = request.get_json()
        channel_identifier = data.get('channel_identifier', '').strip()
        
        print(f"1. Channel identifier: {channel_identifier}")
        
        if not channel_identifier:
            return jsonify({'success': False, 'message': 'Channel identifier is required'})
        
        # Extract channel ID
        channel_id = extract_channel_id(channel_identifier)
        print(f"2. Extracted channel ID: {channel_id}")
        
        if not channel_id:
            return jsonify({'success': False, 'message': 'Invalid YouTube channel identifier'})
        
        # Analyze channel
        print("3. Starting channel analysis...")
        youtube_analyzer = YouTubeAnalyzer(
            os.getenv('YOUTUBE_API_KEY'), 
            db,
            groq_api_key=os.getenv('GROQ_API_KEY')
        )
        
        analysis = youtube_analyzer.analyze_channel_public(channel_id, force_refresh=True)
        print(f"4. Analysis completed. Keys: {list(analysis.keys())}")
        
        # Check if we have basic data
        if 'channel_metrics' in analysis:
            print(f"5. Channel metrics: {analysis['channel_metrics'].get('channel_title', 'Unknown')}")
        else:
            print("5. ERROR: No channel_metrics in analysis")
        
        # Ensure growth predictions are calculated consistently
        if not analysis.get('growth_predictions'):
            analysis['growth_predictions'] = calculate_consistent_growth_predictions(analysis)
            print("6. Added growth predictions")
        
        # Get user data for PDF
        user_data = {
            'name': current_user.name,
            'email': current_user.email,
            'id': current_user.id
        }
        print(f"7. User data: {user_data['name']}")
        
        # Generate PDF
        print("8. Starting PDF generation...")
        from services.pdf_generator import generate_youtube_report_pdf
        
        try:
            pdf_data = generate_youtube_report_pdf(analysis, user_data)
            pdf_size = len(pdf_data)
            print(f"9. PDF generated successfully. Size: {pdf_size} bytes")
            
            # Check if PDF is valid (should be more than 1KB for a real PDF)
            if pdf_size < 1024:
                print(f"10. WARNING: PDF size is too small ({pdf_size} bytes). Might be corrupted.")
                # Let's see what's actually in the data
                try:
                    pdf_content_preview = pdf_data[:200]  # First 200 bytes
                    print(f"11. PDF content preview: {pdf_content_preview}")
                except:
                    print("11. Could not read PDF content")
            
        except Exception as pdf_error:
            print(f"9. ERROR in PDF generation: {str(pdf_error)}")
            import traceback
            print(f"10. Traceback: {traceback.format_exc()}")
            return jsonify({'success': False, 'message': f'Error generating PDF: {str(pdf_error)}'})
        
        # Create response
        from flask import make_response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=youtube_analysis_{channel_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        # Log PDF generation
        logger.info(f"PDF report generated for channel {channel_id} by user {current_user.email}")
        print("=== PDF GENERATION DEBUG END ===")
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        print(f"=== UNEXPECTED ERROR: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Error generating PDF: {str(e)}'})

def calculate_consistent_growth_predictions(analysis):
    """Calculate growth predictions that match what's shown on the website - FIXED"""
    channel_metrics = analysis['channel_metrics']
    engagement_metrics = analysis['engagement_metrics']
    ai_metrics = analysis['ai_enhanced_metrics']
    
    current_subs = channel_metrics.get('subscribers', 0)
    engagement_rate = engagement_metrics.get('avg_engagement_rate', 0)
    consistency = engagement_metrics.get('performance_consistency', 0)
    content_quality = ai_metrics.get('content_quality_score', 0)
    growth_potential = ai_metrics.get('growth_potential', 'Unknown')
    
    # Realistic growth calculation for established channels
    if current_subs >= 1000000:  # 1M+ channels
        base_rate = engagement_rate * 0.4  
    elif current_subs >= 100000:  # 100K-1M channels
        base_rate = engagement_rate * 0.5
    else:  # Smaller channels
        base_rate = engagement_rate * 0.8
    
    # Quality and consistency bonuses
    consistency_bonus = consistency * 0.001
    quality_bonus = content_quality * 0.0005
    
    # Growth potential multiplier
    growth_multiplier = {
        'High': 1.5,
        'Medium': 1.2,
        'Low': 0.8,
        'Very Low': 0.5
    }.get(growth_potential, 1.0)
    
    monthly_growth_rate = (base_rate + consistency_bonus + quality_bonus) * growth_multiplier
    
    # Ensure reasonable bounds
    monthly_growth_rate = max(0.1, min(monthly_growth_rate, 8.0))
    
    # Calculate projections
    return {
        'predicted_monthly_growth_rate': round(monthly_growth_rate, 1),
        'predicted_3month_subs': int(current_subs * (1 + monthly_growth_rate/100) ** 3),
        'predicted_6month_subs': int(current_subs * (1 + monthly_growth_rate/100) ** 6),
        'predicted_12month_subs': int(current_subs * (1 + monthly_growth_rate/100) ** 12)
    }

@app.route('/api/check-analysis-access', methods=['POST'])
def check_analysis_access():
    """Check if user can access analysis features"""
    try:
        data = request.get_json()
        channel_identifier = data.get('channel_identifier', '').strip()
        
        if not channel_identifier:
            return jsonify({'success': False, 'message': 'Channel identifier is required'})
        
        # For now, allow all authenticated users
        if current_user.is_authenticated:
            return jsonify({
                'success': True,
                'has_access': True,
                'message': 'Access granted'
            })
        else:
            return jsonify({
                'success': True,
                'has_access': False,
                'message': 'Please login to download PDF reports'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/reviews')
@login_required
def admin_reviews():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get pending user reviews
    pending_reviews = UserReview.query.filter_by(is_approved=False).order_by(UserReview.created_at.desc()).all()
    
    # Get approved user reviews
    approved_reviews = UserReview.query.filter_by(is_approved=True).order_by(UserReview.created_at.desc()).all()
    
    # Calculate stats
    total_reviews = UserReview.query.count()
    pending_count = len(pending_reviews)
    approved_count = len(approved_reviews)
    today_count = UserReview.query.filter(
        db.func.date(UserReview.created_at) == datetime.utcnow().date()
    ).count()
    
    return render_template('admin/reviews.html',
                         pending_reviews=pending_reviews,
                         approved_reviews=approved_reviews,
                         total_reviews=total_reviews,
                         pending_count=pending_count,
                         approved_count=approved_count,
                         today_count=today_count)

@app.route('/admin/review/approve/<int:review_id>', methods=['POST'])
@login_required
def approve_review(review_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        review = UserReview.query.get_or_404(review_id)
        review.is_approved = True
        review.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Review approved successfully!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error approving review: {str(e)}")
        return jsonify({'success': False, 'message': 'Error approving review'})

@app.route('/admin/review/delete/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        review = UserReview.query.get_or_404(review_id)
        db.session.delete(review)
        db.session.commit()
        flash('Review deleted successfully!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting review: {str(e)}")
        return jsonify({'success': False, 'message': 'Error deleting review'})

@app.route('/admin/review/details/<int:review_id>')
@login_required
def get_review_details(review_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    review = UserReview.query.get_or_404(review_id)
    
    return jsonify({
        'id': review.id,
        'user_name': review.user.name if review.user else 'Unknown User',
        'user_email': review.user.email if review.user else 'No email',
        'user_avatar': review.user.profile_picture if review.user else None,
        'rating': review.rating,
        'comment': review.comment,
        'service_category': review.service_category,
        'is_approved': review.is_approved,
        'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': review.updated_at.strftime('%Y-%m-%d %H:%M:%S') if review.updated_at else None
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            # Get user from PostgreSQL
            user_data = db_manager.get_user_by_email(form.email.data)
            
            if user_data and user_data.provider == 'email':
                # Verify password
                if check_password(form.password.data, user_data.password):
                    user = User(user_data)
                    login_user(user)
                    
                    # Update last login
                    db_manager.update_last_login(user_data.id)
                    
                    flash('Login successful!', 'success')
                    
                    # Redirect to admin panel if admin, else to home
                    if user.role == 'admin':
                        return redirect(url_for('admin_portfolio'))
                    else:
                        return redirect(url_for('index'))
                else:
                    flash('Invalid email or password.', 'danger')
            else:
                flash('Invalid email or password.', 'danger')
                
        except Exception as e:
            flash('An error occurred during login. Please try again.', 'danger')
            print(f'Login error: {str(e)}')
    
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@app.route('/terms-conditions')
def terms_conditions():
    return render_template('terms-conditions.html')

@app.route('/case-studies')
def case_studies():
    return render_template('case-studies.html')

    
@app.route('/admin/contact-submissions')
@login_required
def admin_contact_submissions():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))

    
    submissions = ContactSubmission.query.order_by(ContactSubmission.submitted_at.desc()).all()
    
    # Calculate stats
    today = datetime.utcnow().date()
    today_count = ContactSubmission.query.filter(
        db.func.date(ContactSubmission.submitted_at) == today
    ).count()
    
    company_count = ContactSubmission.query.filter(
        ContactSubmission.company != None,
        ContactSubmission.company != ''
    ).count()
    
    phone_count = ContactSubmission.query.filter(
        ContactSubmission.phone != None, 
        ContactSubmission.phone != ''
    ).count()
    
    return render_template('admin/contact_submissions.html', 
                         submissions=submissions,
                         today_count=today_count,
                         company_count=company_count,
                         phone_count=phone_count)

@app.route('/admin/contact-submission/<int:submission_id>')
@login_required
def get_contact_submission(submission_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    submission = ContactSubmission.query.get_or_404(submission_id)
    
    return jsonify({
        'id': submission.id,
        'name': submission.name,
        'email': submission.email,
        'company': submission.company,
        'phone': submission.phone,
        'service': submission.service,
        'budget': submission.budget,
        'message': submission.message,
        'submitted_at': submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
    })

# Error handlers
@app.errorhandler(Exception)
def handle_all_errors(error):
    """Universal error handler for all HTTP errors"""
    
    # Default error details
    error_messages = {
        400: ("Bad Request", "The request was invalid or cannot be served."),
        401: ("Unauthorized", "Please log in to access this page."),
        403: ("Forbidden", "You don't have permission to access this resource."),
        404: ("Page Not Found", "The page you're looking for doesn't exist."),
        405: ("Method Not Allowed", "This method is not allowed for the requested URL."),
        408: ("Request Timeout", "The request took too long to process."),
        413: ("File Too Large", "The file you uploaded is too large."),
        429: ("Too Many Requests", "You've made too many requests. Please try again later."),
        500: ("Internal Server Error", "Something went wrong on our server."),
        502: ("Bad Gateway", "The server encountered a temporary error."),
        503: ("Service Unavailable", "The service is temporarily unavailable."),
        504: ("Gateway Timeout", "The server took too long to respond.")
    }
    
    # Get error code or default to 500
    error_code = getattr(error, 'code', 500)
    
    # Get error details
    error_title, error_description = error_messages.get(
        error_code, 
        ("Error", "An unexpected error occurred.")
    )
    
    return render_template(
        'error.html',
        error_code=error_code,
        error_title=error_title,
        error_description=error_description,
        error_message=str(error) if app.config['DEBUG'] else None
    ), error_code

# Add database initialization
@app.cli.command("init-db")
def init_db():
    """Initialize the database with sample data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if doesn't exist
        from utils.auth import hash_password
        admin = db_manager.get_user_by_email(os.environ.get('ADMIN_EMAIL'))
        if not admin:
            admin_data = {
                'name': 'Admin User',
                'email': os.environ.get('ADMIN_EMAIL'),
                'password': hash_password(os.environ.get('ADMIN_PASSWORD')),
                'role': 'admin',
                'provider': 'email'
            }
            db_manager.create_user(admin_data)
            print(f"Admin user created: {admin_data['email']} / {os.environ.get('ADMIN_PASSWORD')}")
        
        # Migrate portfolio items from hardcoded JS to database
        if PortfolioItem.query.count() == 0:
            # Keep only the first video as active, convert others to coming soon
            
            
            for item_data in portfolio_data:
                db_manager.save_portfolio_item(item_data)
            print("Portfolio items migrated to database")
        
        print("Database initialized successfully!")

def init_database():
    """Initialize database tables on startup"""
    with app.app_context():
        try:
            # Test database connection first with text() wrapper
            db.session.execute(text('SELECT 1'))
            print("✅ Database connection successful!")
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Create admin user if doesn't exist
            from utils.auth import hash_password
            admin_email = os.environ.get('ADMIN_EMAIL')
            if admin_email:
                admin = db_manager.get_user_by_email(admin_email)
                if not admin:
                    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
                    admin_data = {
                        'name': 'Admin User',
                        'email': admin_email,
                        'password': hash_password(admin_password),
                        'role': 'admin',
                        'provider': 'email'
                    }
                    if db_manager.create_user(admin_data):
                        print(f"✅ Admin user created: {admin_email}")
                    else:
                        print("❌ Failed to create admin user")
                else:
                    print("✅ Admin user already exists")
            
            # Add sample portfolio items if none exist
            if PortfolioItem.query.count() == 0:
                from data.portfolio_data import portfolio_data
                for item_data in portfolio_data:
                    db_manager.save_portfolio_item(item_data)
                print(f"✅ {len(portfolio_data)} sample portfolio items added")
            else:
                print(f"✅ Portfolio items already exist: {PortfolioItem.query.count()} items")
                
        except Exception as e:
            print(f"❌ Database initialization error: {str(e)}")
            import traceback
            traceback.print_exc()

# Call initialization when app starts
init_database()
        
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=os.environ.get('DEBUG', 'False').lower() == 'true')
