from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    occupation = db.Column(db.String(100))  # NEW: User's occupation/role
    profile_picture = db.Column(db.String(255))  # NEW: Path to profile picture
    role = db.Column(db.String(20), default='user')
    provider = db.Column(db.String(20), default='email')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PortfolioItem(db.Model):
    __tablename__ = 'portfolio_items'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    youtube_id = db.Column(db.String(20))
    video_type = db.Column(db.String(20))  # 'youtube', 'instagram', or NULL for coming soon
    category = db.Column(db.String(50), nullable=False)
    tags = db.Column(db.Text)  # Store as JSON string
    status = db.Column(db.String(20), default='active')  # 'active' or 'coming_soon'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'youtube_id': self.youtube_id,
            'video_type': self.video_type,
            'category': self.category,
            'tags': json.loads(self.tags) if self.tags else [],
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ContactSubmission(db.Model):
    __tablename__ = 'contact_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    service = db.Column(db.String(50))
    budget = db.Column(db.String(50))
    message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserReview(db.Model):
    __tablename__ = 'user_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    service_category = db.Column(db.String(100))
    is_approved = db.Column(db.Boolean, default=False)  # Admin must approve before showing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'Anonymous',
            'user_avatar': self.user.profile_picture if self.user else None,
            'rating': self.rating,
            'comment': self.comment,
            'service_category': self.service_category,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class YouTubeAnalyticsSnapshot(db.Model):
    __tablename__ = 'youtube_analytics_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.String(100), nullable=False, index=True)
    snapshot_date = db.Column(db.Date, nullable=False, index=True)
    
    # ==================== BASIC CHANNEL METRICS ====================
    channel_title = db.Column(db.String(200))
    channel_description = db.Column(db.Text)
    channel_custom_url = db.Column(db.String(100))
    channel_country = db.Column(db.String(50))
    channel_published_at = db.Column(db.DateTime)
    
    subscribers = db.Column(db.Integer)
    subscriber_growth = db.Column(db.Integer)
    total_views = db.Column(db.Integer)
    total_videos = db.Column(db.Integer)
    channel_age_days = db.Column(db.Integer)
    hidden_subscribers = db.Column(db.Boolean, default=False)
    
    # ==================== ENGAGEMENT METRICS ====================
    total_likes = db.Column(db.Integer)
    total_comments = db.Column(db.Integer)
    total_engagement = db.Column(db.Integer)
    
    avg_engagement_rate = db.Column(db.Float)
    engagement_consistency = db.Column(db.Float)
    engagement_health = db.Column(db.String(50))
    
    # ==================== VIDEO PERFORMANCE METRICS ====================
    avg_views_per_video = db.Column(db.Float)
    avg_likes_per_video = db.Column(db.Float)
    avg_comments_per_video = db.Column(db.Float)
    avg_duration_seconds = db.Column(db.Float)
    
    top_performing_video_views = db.Column(db.Integer)
    top_performing_video_likes = db.Column(db.Integer)
    top_performing_video_title = db.Column(db.String(300))
    
    performance_consistency = db.Column(db.Float)
    views_std_dev = db.Column(db.Float)
    
    # 🔥 ADD ALL MISSING PERFORMANCE METRICS COLUMNS
    performance_trend = db.Column(db.String(50))
    avg_performance_score = db.Column(db.Float)
    duration_consistency = db.Column(db.Float)
    estimated_retention_rate = db.Column(db.Float)
    content_velocity_score = db.Column(db.Float)
    
    # ==================== CONTENT ANALYSIS ====================
    content_categories = db.Column(db.JSON)
    publishing_frequency = db.Column(db.String(50))
    optimal_video_length = db.Column(db.String(50))
    title_optimization_score = db.Column(db.Float)
    
    # Content gaps identified
    content_gaps = db.Column(db.JSON)
    trending_topics_alignment = db.Column(db.Float)
    
    # ==================== GROWTH & PERFORMANCE ====================
    daily_growth_rate = db.Column(db.Float)
    weekly_growth_rate = db.Column(db.Float)
    monthly_growth_rate = db.Column(db.Float)
    
    growth_momentum = db.Column(db.String(50))
    growth_stage = db.Column(db.String(50))
    
    views_per_subscriber = db.Column(db.Float)
    subscriber_velocity = db.Column(db.Integer)
    
    # ==================== AI-ENHANCED METRICS ====================
    channel_health_score = db.Column(db.Float)
    performance_tier = db.Column(db.String(50))
    content_quality_score = db.Column(db.Float)
    growth_potential = db.Column(db.String(50))
    
    # ==================== DEMOGRAPHIC INFERENCE ====================
    estimated_age_groups = db.Column(db.JSON)
    estimated_gender_ratio = db.Column(db.JSON)
    geographic_distribution = db.Column(db.JSON)
    audience_interests = db.Column(db.JSON)
    audience_education_level = db.Column(db.String(50))
    
    # ==================== AI INSIGHTS & PREDICTIONS ====================
    ai_insights = db.Column(db.JSON)
    growth_predictions = db.Column(db.JSON)
    recommendations = db.Column(db.JSON)
    sentiment_analysis = db.Column(db.JSON)
    
    # ==================== TECHNICAL METADATA ====================
    videos_analyzed = db.Column(db.Integer)
    data_source = db.Column(db.String(50))
    analysis_timestamp = db.Column(db.DateTime)
    
    # Enhanced content metrics
    publishing_consistency = db.Column(db.Float)
    content_diversity_score = db.Column(db.Float)
    content_freshness_score = db.Column(db.Float)
    audience_loyalty_score = db.Column(db.Float)
    algorithm_favorability = db.Column(db.Float)
    # estimated_retention_rate = db.Column(db.Float)  # Already added above
    # content_velocity_score = db.Column(db.Float)    # Already added above
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Index for faster queries
    __table_args__ = (
        db.Index('idx_channel_date', 'channel_id', 'snapshot_date'),
        db.Index('idx_health_score', 'channel_health_score'),
    )
class InstagramAnalyticsSnapshot(db.Model):
    __tablename__ = 'instagram_analytics_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, index=True)
    snapshot_date = db.Column(db.Date, nullable=False, index=True)
    
    # Basic Metrics
    followers = db.Column(db.Integer)
    following = db.Column(db.Integer)
    total_posts = db.Column(db.Integer)
    profile_views = db.Column(db.Integer)
    
    # Engagement Metrics
    avg_engagement_rate = db.Column(db.Float)
    reach = db.Column(db.Integer)
    impressions = db.Column(db.Integer)
    saves = db.Column(db.Integer)
    
    # Content Performance
    reels_performance = db.Column(db.JSON)
    stories_performance = db.Column(db.JSON)
    posts_performance = db.Column(db.JSON)
    highlights_performance = db.Column(db.JSON)
    
    # Audience Insights
    audience_demographics = db.Column(db.JSON)
    audience_locations = db.Column(db.JSON)
    audience_activity = db.Column(db.JSON)
    
    # AI Insights
    ai_insights = db.Column(db.JSON)
    recommendations = db.Column(db.JSON)
    content_strategy = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AnalyticsSettings(db.Model):
    __tablename__ = 'analytics_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)  # 'youtube' or 'instagram'
    identifier = db.Column(db.String(100), nullable=False)  # channel_id or username
    refresh_frequency = db.Column(db.String(50), default='manual')  # 'daily', 'weekly', 'manual'
    last_refresh = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('platform', 'identifier', name='unique_platform_identifier'),
    )
