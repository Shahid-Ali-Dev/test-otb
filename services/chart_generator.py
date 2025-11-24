import os
import io
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF
from reportlab.lib import colors
import logging

logger = logging.getLogger(__name__)

class ChartGenerator:
    def __init__(self):
        # Set style for better looking charts
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def create_performance_radar_chart(self, analysis_data, width=400, height=300):
        """Create a radar chart for performance metrics"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(projection='polar'))
            
            # Metrics for radar chart
            metrics = [
                'Engagement Rate',
                'Consistency', 
                'Content Quality',
                'Growth Potential',
                'Audience Retention',
                'Algorithm Favorability'
            ]
            
            # Get values
            engagement = analysis_data['engagement_metrics'].get('avg_engagement_rate', 0)
            consistency = analysis_data['engagement_metrics'].get('performance_consistency', 0)
            quality = analysis_data['ai_enhanced_metrics'].get('content_quality_score', 0)
            growth = self._convert_growth_to_score(analysis_data['ai_enhanced_metrics'].get('growth_potential', 'Low'))
            retention = analysis_data['performance_metrics'].get('estimated_retention_rate', 0)
            algorithm = analysis_data['ai_enhanced_metrics'].get('algorithm_favorability', 0)
            
            values = [engagement, consistency, quality, growth, retention, algorithm]
            
            # Normalize values to 0-100 scale
            values = [min(v, 100) for v in values]
            
            # Complete the circle
            values += values[:1]
            
            # Angles for each metric
            angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
            angles += angles[:1]
            
            # Plot
            ax.plot(angles, values, 'o-', linewidth=2, label='Your Channel', color='#FF6B35')
            ax.fill(angles, values, alpha=0.25, color='#FF6B35')
            
            # Add metric labels
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(metrics)
            
            # Set y limits and grid
            ax.set_ylim(0, 100)
            ax.set_yticks([20, 40, 60, 80, 100])
            ax.grid(True)
            
            # Add title
            plt.title('Channel Performance Radar', size=14, fontweight='bold', pad=20)
            
            # Save to bytes
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close()
            
            return ImageReader(buffer)
            
        except Exception as e:
            logger.error(f"Error creating radar chart: {str(e)}")
            return self._create_fallback_chart("Radar Chart\nNot Available", width, height)

    def create_engagement_distribution_chart(self, analysis_data, width=400, height=250):
        """Create engagement distribution pie chart"""
        try:
            fig, ax = plt.subplots(figsize=(6, 6))
            
            engagement_metrics = analysis_data['engagement_metrics']
            total_likes = engagement_metrics.get('total_recent_likes', 1)
            total_comments = engagement_metrics.get('total_recent_comments', 1)
            total_shares = max(int(total_likes * 0.1), 1)  # Estimate shares
            
            labels = ['Likes', 'Comments', 'Shares']
            sizes = [total_likes, total_comments, total_shares]
            colors = ['#FF6B35', '#FF8C5A', '#FFA87D']
            explode = (0.1, 0, 0)  # Highlight likes
            
            wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                            autopct='%1.1f%%', shadow=True, startangle=90)
            
            # Style the text
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title('Engagement Distribution', fontweight='bold', pad=20)
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close()
            
            return ImageReader(buffer)
            
        except Exception as e:
            logger.error(f"Error creating engagement chart: {str(e)}")
            return self._create_fallback_chart("Engagement Chart\nNot Available", width, height)

    def create_growth_prediction_chart(self, analysis_data, width=500, height=300):
        """Create growth prediction line chart"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            predictions = analysis_data.get('growth_predictions', {})
            current_subs = analysis_data['channel_metrics'].get('subscribers', 0)
            
            if not predictions:
                return self._create_fallback_chart("Growth Data\nNot Available", width, height)
            
            # Timeline data
            months = ['Current', '1 Month', '3 Months', '6 Months', '1 Year']
            subscribers = [
                current_subs,
                predictions.get('predicted_3month_subs', current_subs * 1.05),
                predictions.get('predicted_3month_subs', current_subs * 1.15),
                predictions.get('predicted_6month_subs', current_subs * 1.3),
                predictions.get('predicted_12month_subs', current_subs * 1.5)
            ]
            
            # Convert to thousands for better display
            subs_in_k = [s/1000 for s in subscribers]
            
            # Create line plot
            ax.plot(months, subs_in_k, marker='o', linewidth=3, markersize=8, 
                   color='#FF6B35', markerfacecolor='white', markeredgewidth=2)
            
            # Fill under the line
            ax.fill_between(months, subs_in_k, alpha=0.3, color='#FF6B35')
            
            # Customize the chart
            ax.set_ylabel('Subscribers (Thousands)', fontweight='bold')
            ax.set_xlabel('Timeline', fontweight='bold')
            ax.set_title('Subscriber Growth Projection', fontsize=14, fontweight='bold', pad=20)
            
            # Add grid
            ax.grid(True, alpha=0.3)
            
            # Add value annotations
            for i, v in enumerate(subs_in_k):
                ax.annotate(f'{v:.1f}K', (i, v), textcoords="offset points", 
                           xytext=(0,10), ha='center', fontweight='bold')
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close()
            
            return ImageReader(buffer)
            
        except Exception as e:
            logger.error(f"Error creating growth chart: {str(e)}")
            return self._create_fallback_chart("Growth Chart\nNot Available", width, height)

    def create_performance_comparison_chart(self, analysis_data, width=500, height=300):
        """Create performance comparison bar chart"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Your channel metrics
            your_metrics = [
                analysis_data['engagement_metrics'].get('avg_engagement_rate', 0),
                analysis_data['ai_enhanced_metrics'].get('content_quality_score', 0),
                analysis_data['engagement_metrics'].get('performance_consistency', 0),
                analysis_data['performance_metrics'].get('estimated_retention_rate', 0)
            ]
            
            # YouTube average benchmarks
            youtube_averages = [4.5, 60, 65, 50]
            
            labels = ['Engagement Rate', 'Content Quality', 'Consistency', 'Retention']
            x = np.arange(len(labels))
            width_bar = 0.35
            
            # Create bars
            bars1 = ax.bar(x - width_bar/2, your_metrics, width_bar, label='Your Channel', 
                          color='#FF6B35', alpha=0.8)
            bars2 = ax.bar(x + width_bar/2, youtube_averages, width_bar, label='YouTube Average', 
                          color='#6C757D', alpha=0.8)
            
            # Customize chart
            ax.set_ylabel('Score (%)', fontweight='bold')
            ax.set_title('Performance vs YouTube Average', fontsize=14, fontweight='bold', pad=20)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            def add_value_labels(bars):
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height:.1f}%',
                               xy=(bar.get_x() + bar.get_width() / 2, height),
                               xytext=(0, 3),
                               textcoords="offset points",
                               ha='center', va='bottom', fontweight='bold')
            
            add_value_labels(bars1)
            add_value_labels(bars2)
            
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close()
            
            return ImageReader(buffer)
            
        except Exception as e:
            logger.error(f"Error creating comparison chart: {str(e)}")
            return self._create_fallback_chart("Comparison Chart\nNot Available", width, height)

    def _convert_growth_to_score(self, growth_potential):
        """Convert growth potential to numerical score"""
        growth_scores = {
            'High': 85,
            'Medium': 65,
            'Low': 40,
            'Unknown': 50
        }
        return growth_scores.get(growth_potential, 50)

    def _create_fallback_chart(self, message, width, height):
        """Create a fallback chart when data is unavailable"""
        try:
            fig, ax = plt.subplots(figsize=(width/100, height/100))
            ax.text(0.5, 0.5, message, ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            ax.set_xticks([])
            ax.set_yticks([])
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close()
            
            return ImageReader(buffer)
        except:
            # Ultimate fallback - return None
            return None