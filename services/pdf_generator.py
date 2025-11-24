import os
import io
import requests
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image, PageBreak, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfdoc
import logging

logger = logging.getLogger(__name__)

class YouTubeReportPDF:
    def __init__(self, analysis_data, user_data=None):
        self.analysis = analysis_data
        self.user_data = user_data
        self.buffer = io.BytesIO()
        
        # Use A4 with optimized margins
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=54,
            leftMargin=54,
            topMargin=72,
            bottomMargin=90,  # Increased bottom margin for footer
            title=f"YouTube Analysis - {analysis_data['channel_metrics'].get('channel_title', 'Unknown Channel')}"
        )
        
        self.styles = getSampleStyleSheet()
        self.story = []
        
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles with better formatting"""
        self.styles = getSampleStyleSheet()
        
        # Add footer style
        footer_style = ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=0
        )
        self.styles.add(footer_style)
        
        # Add note style
        note_style = ParagraphStyle(
            name='Note',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#666666'),
            alignment=TA_JUSTIFY,
            spaceBefore=5,
            spaceAfter=5,
            leading=9
        )
        self.styles.add(note_style)

        custom_styles_config = [
            {
                'name': 'CoverTitle',
                'parent': 'Title',
                'fontSize': 28,
                'textColor': colors.HexColor('#FF6B35'),
                'alignment': TA_CENTER,
                'spaceAfter': 30,
                'spaceBefore': 40,
                'fontName': 'Helvetica-Bold',
                'leading': 32
            },
            {
                'name': 'CoverSubtitle', 
                'parent': 'Normal',
                'fontSize': 14,
                'textColor': colors.HexColor('#666666'),
                'alignment': TA_CENTER,
                'spaceAfter': 20,
                'leading': 18
            },
            {
                'name': 'SectionTitle',
                'parent': 'Heading1',
                'fontSize': 16,
                'textColor': colors.HexColor('#FF6B35'),
                'spaceAfter': 20,
                'spaceBefore': 25,
                'fontName': 'Helvetica-Bold',
                'leading': 20,
                'backColor': colors.HexColor('#FFF5F2'),
                'borderPadding': 10,
                'leftIndent': 0
            },
            {
                'name': 'BodyText',
                'parent': 'Normal',
                'fontSize': 9,
                'textColor': colors.black,
                'alignment': TA_JUSTIFY,
                'spaceAfter': 8,
                'leading': 12,
                'wordWrap': 'LTR',
                'splitLongWords': True,
            },
            {
                'name': 'SubsectionTitle',
                'parent': 'Normal',
                'fontSize': 12,
                'textColor': colors.HexColor('#1E3A5F'),
                'fontName': 'Helvetica-Bold',
                'spaceAfter': 10,
                'spaceBefore': 15,
                'leftIndent': 0,
                'backColor': colors.HexColor('#F0F4F8'),
                'borderPadding': 8,
                'borderColor': colors.HexColor('#D1DDE9'),
                'borderWidth': 1,
                'alignment': TA_LEFT
            },
            {
                'name': 'InsightTitle',
                'parent': 'Normal',
                'fontSize': 12,
                'textColor': colors.HexColor('#1E3A5F'),
                'fontName': 'Helvetica-Bold',
                'spaceAfter': 10,
                'spaceBefore': 15,
                'backColor': colors.HexColor('#F0F4F8'),
                'borderPadding': 8,
                'borderColor': colors.HexColor('#D1DDE9'),
                'borderWidth': 1,
                'leftIndent': 0,
                'alignment': TA_LEFT
            },
            {
                'name': 'ActionPlanTitle',
                'parent': 'Normal',
                'fontSize': 11,
                'textColor': colors.HexColor('#2C5530'),
                'fontName': 'Helvetica-Bold',
                'spaceAfter': 8,
                'spaceBefore': 12,
                'backColor': colors.HexColor('#F0F7F4'),
                'borderPadding': 8,
                'borderColor': colors.HexColor('#C8E6C9'),
                'borderWidth': 1,
                'alignment': TA_LEFT
            },
            {
                'name': 'BulletText',
                'parent': 'Normal',
                'fontSize': 9,
                'textColor': colors.black,
                'spaceAfter': 4,
                'leading': 11,
                'leftIndent': 0
            }
        ]
        
        for style_config in custom_styles_config:
            try:
                parent_style = self.styles[style_config['parent']]
                style = ParagraphStyle(
                    name=style_config['name'],
                    parent=parent_style,
                    fontSize=style_config.get('fontSize', 10),
                    textColor=style_config.get('textColor', colors.black),
                    alignment=style_config.get('alignment', TA_LEFT),
                    spaceAfter=style_config.get('spaceAfter', 12),
                    spaceBefore=style_config.get('spaceBefore', 0),
                    fontName=style_config.get('fontName', 'Helvetica'),
                    leading=style_config.get('leading', 14),
                    leftIndent=style_config.get('leftIndent', 0),
                    backColor=style_config.get('backColor', None),
                    borderPadding=style_config.get('borderPadding', 0),
                    borderColor=style_config.get('borderColor', None),
                    borderWidth=style_config.get('borderWidth', 0),
                    wordWrap=style_config.get('wordWrap', 'LTR'),
                    splitLongWords=style_config.get('splitLongWords', False)
                )
                self.styles.add(style)
            except Exception as e:
                logger.warning(f"Could not create style {style_config['name']}: {str(e)}")

    def _add_footer(self, canvas, doc):
        """Add footer with website logo, link, and caution note to every page"""
        try:
            # Save the current state
            canvas.saveState()
            
            # Set footer style
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.HexColor('#666666'))
            
            # Get page dimensions
            page_width = doc.pagesize[0]
            page_height = doc.pagesize[1]
            
            # Footer content - centered
            footer_y = 30
            
            try:
                # Try to load the website logo from images folder
                logo_path = os.path.join('static', 'images', 'Asset 22.png')
                if os.path.exists(logo_path):
                    # Add logo image - LOWERED THE Y POSITION by 2 pixels
                    logo = Image(logo_path, width=12, height=12)
                    logo.drawOn(canvas, page_width/2 - 45, footer_y - 4)  # Changed from -2 to -4
                    
                    # Add website text with link
                    canvas.setFillColor(colors.blue)
                    canvas.drawString(page_width/2 - 30, footer_y, "www.shoutotb.com")
                    
                    # Add URL link annotation (makes it clickable in PDF)
                    canvas.linkURL(
                        "https://www.shoutotb.com",
                        (page_width/2 - 45, footer_y - 5, page_width/2 + 60, footer_y + 10),
                        relative=1
                    )
                else:
                    # Fallback: use emoji if logo not found
                    canvas.drawCentredString(page_width / 2, footer_y, "🌐 www.shoutotb.com")
                    
                    # Add URL link annotation for emoji version
                    canvas.linkURL(
                        "https://www.shoutotb.com",
                        (page_width/2 - 50, footer_y - 5, page_width/2 + 50, footer_y + 10),
                        relative=1
                    )
                    
            except Exception as logo_error:
                logger.warning(f"Could not add logo: {str(logo_error)}")
                # Fallback to text only
                canvas.drawCentredString(page_width / 2, footer_y, "🌐 www.shoutotb.com")
                canvas.linkURL(
                    "https://www.shoutotb.com",
                    (page_width/2 - 50, footer_y - 5, page_width/2 + 50, footer_y + 10),
                    relative=1
                )
            
            # Add professional note on ALL pages (smaller text)
            note_text = "Note: Analysis generated using automated tools. Insights should be considered as guidance rather than definitive conclusions."
            canvas.setFont('Helvetica', 6)
            canvas.setFillColor(colors.HexColor('#999999'))
            
            # Draw note above the footer
            canvas.drawCentredString(page_width / 2, footer_y + 15, note_text)
            
            canvas.restoreState()
            
        except Exception as e:
            logger.warning(f"Could not add footer: {str(e)}")
            # Basic fallback
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.HexColor('#666666'))
            canvas.drawCentredString(doc.pagesize[0] / 2, 30, "www.shoutotb.com")
            canvas.restoreState()

    def _download_image_safe(self, url, max_size=(120, 120)):
        """Safely download and resize image with error handling"""
        try:
            if not url:
                return None
                
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img_data = io.BytesIO(response.content)
                
                # Import PIL here to avoid issues if not available
                try:
                    from PIL import Image as PILImage
                    img = PILImage.open(img_data)
                    
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    # Resize if too large
                    img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
                    
                    # Save to bytes
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=85)
                    output.seek(0)
                    return output
                except ImportError:
                    # PIL not available, return original image data
                    return img_data
                    
        except Exception as e:
            logger.warning(f"Could not download image {url}: {str(e)}")
        return None

    def _get_safe_data(self, data_path, default=''):
        """Safely get nested data with fallbacks"""
        try:
            keys = data_path.split('.')
            value = self.analysis
            for key in keys:
                value = value.get(key, {})
            return value if value != {} else default
        except (AttributeError, KeyError, TypeError):
            return default

    def _format_number_safe(self, num):
        """Safely format numbers with K/M suffixes"""
        try:
            if not num:
                return '0'
            num = int(num)
            if num >= 1000000:
                return f"{num/1000000:.1f}M"
            elif num >= 1000:
                return f"{num/1000:.1f}K"
            return str(num)
        except (ValueError, TypeError):
            return '0'

    def _wrap_text_safe(self, text, max_length=60):
        """Safely wrap text to specified maximum length"""
        if not text:
            return ''
        try:
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                if len(' '.join(current_line + [word])) <= max_length:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return '<br/>'.join(lines)
        except:
            return str(text)[:max_length] if text else ''

    def _shorten_video_length(self, length_text):
        """Shorten video length descriptions"""
        if not length_text:
            return 'Unknown'
        
        length_lower = length_text.lower()
        if 'very long' in length_lower or '30+' in length_lower:
            return 'Very Long'
        elif 'long' in length_lower or '15-30' in length_lower:
            return 'Long'
        elif 'medium' in length_lower or '8-15' in length_lower:
            return 'Medium'
        elif 'short' in length_lower or '4-8' in length_lower:
            return 'Short'
        elif 'very short' in length_lower or '1-4' in length_lower:
            return 'Very Short'
        else:
            return str(length_text)[:15]

    def _create_cover_page(self):
        """Create professional cover page"""
        try:
            # Title
            title = Paragraph("YouTube Channel Analysis Report", self.styles['CoverTitle'])
            self.story.append(title)
            
            # Channel title
            channel_title = self._get_safe_data('channel_metrics.channel_title', 'Unknown Channel')
            channel_para = Paragraph(channel_title, self.styles['CoverSubtitle'])
            self.story.append(channel_para)
            
            self.story.append(Spacer(1, 30))
            
            # Channel thumbnail if available
            thumbnail_url = self._get_safe_data('channel_metrics.thumbnail_url')
            if thumbnail_url:
                img_data = self._download_image_safe(thumbnail_url, (100, 100))
                if img_data:
                    try:
                        channel_img = Image(img_data, width=80, height=80)
                        channel_img.hAlign = 'CENTER'
                        self.story.append(channel_img)
                        self.story.append(Spacer(1, 20))
                    except Exception as e:
                        logger.warning(f"Could not add channel thumbnail: {str(e)}")
            
            # Analysis details
            analysis_date = datetime.now().strftime("%B %d, %Y")
            date_para = Paragraph(f"Analysis Date: {analysis_date}", self.styles['CoverSubtitle'])
            self.story.append(date_para)
            
            # Generated by
            if self.user_data:
                user_text = f"Generated for: {self.user_data.get('name', 'User')}"
                user_para = Paragraph(user_text, self.styles['CoverSubtitle'])
                self.story.append(user_para)
            
            self.story.append(Spacer(1, 40))
            
            # Quick stats table
            stats_data = [
                ['Subscribers', 'Total Views', 'Videos'],
                [
                    self._format_number_safe(self._get_safe_data('channel_metrics.subscribers')),
                    self._format_number_safe(self._get_safe_data('channel_metrics.total_views')),
                    self._format_number_safe(self._get_safe_data('channel_metrics.total_videos'))
                ]
            ]
            
            stats_table = Table(stats_data, colWidths=[1.6*inch, 1.6*inch, 1.6*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, 1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F8F9FA')),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            self.story.append(stats_table)
            
            self.story.append(PageBreak())
            
        except Exception as e:
            logger.error(f"Error in cover page: {str(e)}")
            self.story.append(Paragraph("YouTube Analysis Report", self.styles['Title']))
            self.story.append(PageBreak())

    def _create_executive_summary(self):
        """Create executive summary with CONSISTENT metrics"""
        try:
            title = Paragraph("Executive Summary", self.styles['SectionTitle'])
            self.story.append(title)
            
            # 🔥 USE CONSISTENT METRIC SOURCES
            health_score = self._get_safe_data('ai_enhanced_metrics.channel_health_score', 0)
            performance_tier = self._get_safe_data('ai_enhanced_metrics.performance_tier', 'Unknown')
            engagement_rate = self._get_safe_data('engagement_metrics.avg_engagement_rate', 0)
            content_quality = self._get_safe_data('ai_enhanced_metrics.content_quality_score', 0)
            growth_potential = self._get_safe_data('ai_enhanced_metrics.growth_potential', 'Unknown')
            
            # 🔥 GET CORRECT TOP VIDEO DATA
            top_video_views = self._get_safe_data('engagement_metrics.top_performing_video_views', 0)
            subscribers = self._get_safe_data('channel_metrics.subscribers', 1)
            viral_ratio = top_video_views / subscribers if subscribers > 0 else 0
            
            summary_text = f"""
            This analysis provides a comprehensive overview of your YouTube channel's performance, 
            content strategy, and growth potential. Your channel has a health score of <b>{health_score}/100</b> 
            and is currently performing at a <b>{performance_tier}</b> level with an engagement rate of <b>{engagement_rate:.1f}%</b>.
            """
            
            # 🔥 ADD VIRAL PERFORMANCE CONTEXT
            if viral_ratio > 10:
                summary_text += f" Your top video shows exceptional viral potential with <b>{viral_ratio:.1f}X</b> more views than subscribers."
            elif viral_ratio > 3:
                summary_text += f" Your content demonstrates good reach with a <b>{viral_ratio:.1f}X</b> viral ratio on top videos."
                
            summary_para = Paragraph(summary_text, self.styles['BodyText'])
            self.story.append(summary_para)
            self.story.append(Spacer(1, 12))
            
            # Key metrics table
            metrics_data = [
                ['Metric', 'Your Score', 'Assessment'],
                [
                    'Engagement Rate', 
                    f"{engagement_rate:.1f}%",
                    self._get_engagement_assessment(engagement_rate)
                ],
                [
                    'Content Quality',
                    f"{self._get_safe_data('ai_enhanced_metrics.content_quality_score', 0)}/100",
                    self._get_quality_assessment(self._get_safe_data('ai_enhanced_metrics.content_quality_score', 0))
                ],
                [
                    'Growth Potential',
                    self._get_safe_data('ai_enhanced_metrics.growth_potential', 'Unknown'),
                    self._get_growth_assessment(self._get_safe_data('ai_enhanced_metrics.growth_potential', 'Unknown'))
                ]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[1.6*inch, 1.2*inch, 2.2*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5AA0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            self.story.append(metrics_table)
            
            self.story.append(Spacer(1, 20))
            
        except Exception as e:
            logger.error(f"Error in executive summary: {str(e)}")
            self.story.append(Paragraph("Executive Summary - Data Unavailable", self.styles['Normal']))

    def _create_channel_profile(self):
        """Create channel profile section"""
        try:
            title = Paragraph("Channel Profile", self.styles['SectionTitle'])
            self.story.append(title)
            
            profile_data = [
                ['Channel Title', self._wrap_text_safe(self._get_safe_data('channel_metrics.channel_title'), 35)],
                ['Subscribers', self._format_number_safe(self._get_safe_data('channel_metrics.subscribers'))],
                ['Total Views', self._format_number_safe(self._get_safe_data('channel_metrics.total_views'))],
                ['Total Videos', self._format_number_safe(self._get_safe_data('channel_metrics.total_videos'))],
                ['Channel Age', f"{self._get_safe_data('channel_metrics.channel_age_days', 0)} days"],
                ['Country', self._get_safe_data('channel_metrics.country', 'Unknown')],
                ['Verified', 'Yes' if self._get_safe_data('channel_metrics.is_verified') else 'No']
            ]
            
            custom_url = self._get_safe_data('channel_metrics.custom_url')
            if custom_url:
                youtube_url = f"https://youtube.com/{custom_url}"
                profile_data.append(['YouTube Channel', self._wrap_text_safe(youtube_url, 35)])
            
            profile_table = Table(profile_data, colWidths=[1.8*inch, 3.2*inch])
            profile_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            self.story.append(profile_table)
            
            self.story.append(Spacer(1, 15))
            
            description = self._get_safe_data('channel_metrics.channel_description')
            if description and description != 'No description available.':
                desc_title = Paragraph("Channel Description:", self.styles['Normal'])
                self.story.append(desc_title)
                
                wrapped_description = self._wrap_text_safe(description, 70)
                desc_para = Paragraph(wrapped_description, self.styles['BodyText'])
                self.story.append(desc_para)
                self.story.append(Spacer(1, 15))
                
        except Exception as e:
            logger.error(f"Error in channel profile: {str(e)}")

    def _create_performance_metrics(self):
        """Create performance metrics section"""
        try:
            title = Paragraph("Performance Metrics", self.styles['SectionTitle'])
            self.story.append(title)
            
            # Use shortened video length
            optimal_length = self._shorten_video_length(
                self._get_safe_data('performance_metrics.optimal_video_length', 'Unknown')
            )
            
            metrics = [
                ('Engagement Rate', f"{self._get_safe_data('engagement_metrics.avg_engagement_rate', 0):.1f}%"),
                ('Channel Health', f"{self._get_safe_data('ai_enhanced_metrics.channel_health_score', 0)}/100"),
                ('Performance Consistency', f"{self._get_safe_data('engagement_metrics.performance_consistency', 0):.1f}%"),
                ('Content Quality', f"{self._get_safe_data('ai_enhanced_metrics.content_quality_score', 0)}/100"),
                ('Content Velocity', f"{self._get_safe_data('performance_metrics.content_velocity_score', 0)}/100"),
                ('Audience Retention', f"{self._get_safe_data('performance_metrics.estimated_retention_rate', 0):.1f}%"),
                ('Optimal Video Length', optimal_length),
                ('Growth Potential', self._get_safe_data('ai_enhanced_metrics.growth_potential', 'Unknown'))
            ]
            
            metrics_data = []
            for i in range(0, len(metrics), 2):
                row = []
                if i < len(metrics):
                    row.extend(metrics[i])
                else:
                    row.extend(['', ''])
                
                if i + 1 < len(metrics):
                    row.extend(metrics[i + 1])
                else:
                    row.extend(['', ''])
                
                metrics_data.append(row)
            
            metrics_table = Table(metrics_data, colWidths=[2.0*inch, 0.8*inch, 2.0*inch, 0.8*inch])
            metrics_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            self.story.append(metrics_table)
            
            self.story.append(Spacer(1, 20))
            
        except Exception as e:
            logger.error(f"Error in performance metrics: {str(e)}")

    def _create_ai_insights(self):
        """Create AI insights section with better formatting"""
        try:
            title = Paragraph("AI-Powered Insights", self.styles['SectionTitle'])
            self.story.append(title)
            
            insights = self._get_safe_data('ai_insights', [])
            
            if not insights:
                no_insights = Paragraph("No AI insights available for this analysis.", self.styles['BodyText'])
                self.story.append(no_insights)
                return
            
            for i, insight in enumerate(insights[:3]):
                # Use the new InsightTitle style with blue background
                insight_title = f"{insight.get('title', f'Insight #{i+1}')}"
                title_para = Paragraph(insight_title, self.styles['InsightTitle'])
                self.story.append(title_para)
                
                # Description with better spacing
                description = insight.get('description', 'No description available.')
                wrapped_desc = self._wrap_text_safe(description, 75)
                desc_para = Paragraph(wrapped_desc, self.styles['BodyText'])
                self.story.append(desc_para)
                
                # Confidence and priority with less space
                confidence = int(insight.get('confidence', 0.8) * 100)
                priority = insight.get('priority', 'medium').upper()
                
                meta_text = f"<b>Confidence:</b> {confidence}% | <b>Priority:</b> {priority}"
                meta_para = Paragraph(meta_text, self.styles['BodyText'])
                self.story.append(meta_para)
                
                # Actionable steps with better formatting
                steps = insight.get('actionable_steps', [])
                if steps:
                    steps_title = Paragraph("<b>Actionable Steps:</b>", self.styles['BodyText'])
                    self.story.append(steps_title)
                    
                    step_items = []
                    for step in steps[:3]:
                        wrapped_step = self._wrap_text_safe(step, 65)
                        step_items.append(ListItem(Paragraph(wrapped_step, self.styles['BulletText'])))
                    
                    steps_list = ListFlowable(step_items, bulletType='bullet', leftIndent=15)
                    self.story.append(steps_list)
                
                # Add consistent spacing between insights
                if i < len(insights[:3]) - 1:  # Don't add after last insight
                    self.story.append(Spacer(1, 15))
                
        except Exception as e:
            logger.error(f"Error in AI insights: {str(e)}")

    def _create_recommendations(self):
        """Create strategic recommendations section"""
        try:
            title = Paragraph("Strategic Recommendations", self.styles['SectionTitle'])
            self.story.append(title)
            
            recommendations = self._get_safe_data('recommendations', [])
            
            if not recommendations:
                no_recs = Paragraph("No recommendations available for this analysis.", self.styles['BodyText'])
                self.story.append(no_recs)
                return
            
            for i, rec in enumerate(recommendations[:3]):
                # Use SubsectionTitle for consistent blue styling
                rec_title = f"{rec.get('title', f'Recommendation #{i+1}')}"
                title_para = Paragraph(rec_title, self.styles['SubsectionTitle'])
                self.story.append(title_para)
                
                # Description
                description = rec.get('description', 'No description available.')
                wrapped_desc = self._wrap_text_safe(description, 70)
                desc_para = Paragraph(wrapped_desc, self.styles['BodyText'])
                self.story.append(desc_para)
                
                # Priority
                priority = rec.get('priority', 'medium').upper()
                priority_text = f"<b>Priority:</b> {priority}"
                priority_para = Paragraph(priority_text, self.styles['BodyText'])
                self.story.append(priority_para)
                
                # Actionable steps
                steps = rec.get('actionable_steps', [])
                if steps:
                    steps_title = Paragraph("<b>Implementation Steps:</b>", self.styles['BodyText'])
                    self.story.append(steps_title)
                    
                    step_items = []
                    for step in steps[:3]:
                        wrapped_step = self._wrap_text_safe(step, 65)
                        step_items.append(ListItem(Paragraph(wrapped_step, self.styles['BulletText'])))
                    
                    steps_list = ListFlowable(step_items, bulletType='bullet', leftIndent=15)
                    self.story.append(steps_list)
                
                # Expected impact and timeline
                expected_impact = rec.get('expected_impact', 'Improved channel performance')
                timeline = rec.get('timeline', 'short-term')
                
                impact_text = f"<b>Expected Impact:</b> {expected_impact} | <b>Timeline:</b> {timeline}"
                impact_para = Paragraph(impact_text, self.styles['BodyText'])
                self.story.append(impact_para)
                
                # Consistent spacing between recommendations
                if i < len(recommendations[:3]) - 1:
                    self.story.append(Spacer(1, 15))
                
        except Exception as e:
            logger.error(f"Error in recommendations: {str(e)}")

    def _create_growth_predictions(self):
        """Create growth predictions section"""
        try:
            title = Paragraph("Growth Predictions", self.styles['SectionTitle'])
            self.story.append(title)
            
            predictions = self._get_safe_data('growth_predictions', {})
            current_subs = self._get_safe_data('channel_metrics.subscribers', 0)
            
            if not predictions:
                engagement_rate = self._get_safe_data('engagement_metrics.avg_engagement_rate', 0)
                monthly_growth_rate = max(0.5, min(engagement_rate * 0.8, 15.0))
                
                predictions = {
                    'predicted_monthly_growth_rate': monthly_growth_rate,
                    'predicted_3month_subs': int(current_subs * (1 + monthly_growth_rate/100) ** 3),
                    'predicted_6month_subs': int(current_subs * (1 + monthly_growth_rate/100) ** 6),
                    'predicted_12month_subs': int(current_subs * (1 + monthly_growth_rate/100) ** 12)
                }
            
            growth_rate = predictions.get('predicted_monthly_growth_rate', 0)
            
            summary_text = f"""
            Based on current performance metrics and engagement patterns, your channel is projected 
            to grow at approximately <b>{growth_rate:.1f}% per month</b>. This projection considers your 
            current engagement rate and content performance trends.
            """
            
            summary_para = Paragraph(summary_text, self.styles['BodyText'])
            self.story.append(summary_para)
            self.story.append(Spacer(1, 12))
            
            projections_data = [
                ['Timeline', 'Projected Subscribers', 'Growth'],
                [
                    'Current', 
                    self._format_number_safe(current_subs),
                    'Baseline'
                ],
                [
                    '3 Months', 
                    self._format_number_safe(predictions.get('predicted_3month_subs', current_subs)),
                    f"+{self._format_number_safe(predictions.get('predicted_3month_subs', current_subs) - current_subs)}"
                ],
                [
                    '6 Months', 
                    self._format_number_safe(predictions.get('predicted_6month_subs', current_subs)),
                    f"+{self._format_number_safe(predictions.get('predicted_6month_subs', current_subs) - current_subs)}"
                ],
                [
                    '1 Year', 
                    self._format_number_safe(predictions.get('predicted_12month_subs', current_subs)),
                    f"+{self._format_number_safe(predictions.get('predicted_12month_subs', current_subs) - current_subs)}"
                ]
            ]
            
            projections_table = Table(projections_data, colWidths=[1.4*inch, 1.8*inch, 1.4*inch])
            projections_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5AA0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ]))
            self.story.append(projections_table)
            
            self.story.append(Spacer(1, 20))
            
        except Exception as e:
            logger.error(f"Error in growth predictions: {str(e)}")

    def _create_action_plan(self):
        """Create 30-60-90 day action plan with better formatting"""
        try:
            title = Paragraph("30-60-90 Day Action Plan", self.styles['SectionTitle'])
            self.story.append(title)
            
            # Phase 1: First 30 Days
            phase1_title = Paragraph("First 30 Days (Quick Wins)", self.styles['ActionPlanTitle'])
            self.story.append(phase1_title)
            
            phase1_text = """
            • Implement top 3 actionable steps from AI insights<br/>
            • Optimize video titles and descriptions for SEO<br/>
            • Engage with audience comments daily<br/>
            • Analyze top-performing content patterns
            """
            phase1_para = Paragraph(phase1_text, self.styles['BodyText'])
            self.story.append(phase1_para)
            self.story.append(Spacer(1, 8))
            
            # Phase 2: 31-60 Days
            phase2_title = Paragraph("31-60 Days (Strategic Improvements)", self.styles['ActionPlanTitle'])
            self.story.append(phase2_title)
            
            phase2_text = """
            • Implement content strategy recommendations<br/>
            • Test new content formats based on performance data<br/>
            • Improve audience retention through better editing<br/>
            • Build content calendar for consistency
            """
            phase2_para = Paragraph(phase2_text, self.styles['BodyText'])
            self.story.append(phase2_para)
            self.story.append(Spacer(1, 8))
            
            # Phase 3: 61-90 Days
            phase3_title = Paragraph("61-90 Days (Growth Acceleration)", self.styles['ActionPlanTitle'])
            self.story.append(phase3_title)
            
            phase3_text = """
            • Scale successful content formats<br/>
            • Explore collaboration opportunities<br/>
            • Implement advanced audience growth strategies<br/>
            • Monitor and adjust based on performance metrics
            """
            phase3_para = Paragraph(phase3_text, self.styles['BodyText'])
            self.story.append(phase3_para)
            
            self.story.append(Spacer(1, 15))
            
        except Exception as e:
            logger.error(f"Error in action plan: {str(e)}")

    def _get_engagement_assessment(self, rate):
        rate = float(rate or 0)
        if rate >= 8: return "Excellent"
        elif rate >= 5: return "Good"
        elif rate >= 3: return "Average"
        else: return "Needs improvement"

    def _get_quality_assessment(self, score):
        score = int(score or 0)
        if score >= 80: return "High quality"
        elif score >= 60: return "Good quality"
        else: return "Needs improvement"

    def _get_growth_assessment(self, potential):
        potential = str(potential or 'Unknown')
        if potential == 'High': return "Strong growth"
        elif potential == 'Medium': return "Steady growth"
        else: return "Foundation phase"

    def generate_pdf(self):
        """Generate the complete PDF report"""
        try:
            self._create_cover_page()
            self._create_executive_summary()
            self._create_channel_profile()
            self._create_performance_metrics()
            self._create_ai_insights()
            self._create_recommendations()
            self._create_growth_predictions()
            self._create_action_plan()
            
            # Build with footer on every page
            self.doc.build(self.story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)
            pdf_data = self.buffer.getvalue()
            self.buffer.close()
            
            return pdf_data
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            try:
                error_buffer = io.BytesIO()
                error_doc = SimpleDocTemplate(error_buffer, pagesize=A4)
                error_story = []
                error_story.append(Paragraph("PDF Generation Error", self.styles['Title']))
                error_story.append(Paragraph("There was an error generating the comprehensive report.", self.styles['Normal']))
                error_doc.build(error_story)
                return error_buffer.getvalue()
            except:
                # Fixed escape sequence
                return b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources << >>\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n180\n%%EOF'

def generate_youtube_report_pdf(analysis_data, user_data=None):
    """Main function to generate YouTube analysis PDF report"""
    try:
        generator = YouTubeReportPDF(analysis_data, user_data)
        pdf_data = generator.generate_pdf()
        return pdf_data
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {str(e)}")
        raise e