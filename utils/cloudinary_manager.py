# cloudinary_manager.py - ENHANCED VERSION (Preserves SERVICE_DATA)
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from pathlib import Path
import json
import re

class CloudinaryManager:
    @staticmethod
    def configure():
        """Configure Cloudinary with credentials from environment variables"""
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
            api_key=os.environ.get('CLOUDINARY_API_KEY'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
            secure=True
        )

    @staticmethod
    def test_connection():
        """Test Cloudinary connection (for debugging)"""
        try:
            CloudinaryManager.configure()
            cloudinary.api.ping()
            print("✅ Cloudinary connection successful!")
            return True
        except Exception as e:
            print(f"❌ Cloudinary connection failed: {str(e)}")
            return False

    @staticmethod
    def delete_all_service_videos():
        """Delete ALL service videos from Cloudinary to start fresh"""
        try:
            CloudinaryManager.configure()
            print("🗑️  Deleting all existing service videos from Cloudinary...")
            
            # List all videos in the service-animations folder
            result = cloudinary.api.resources(
                type="upload",
                resource_type="video",
                prefix="shout-otb/service-animations",
                max_results=100
            )
            
            deleted_count = 0
            for resource in result.get('resources', []):
                public_id = resource['public_id']
                try:
                    # Delete the resource
                    delete_result = cloudinary.uploader.destroy(public_id, resource_type="video")
                    if delete_result.get('result') == 'ok':
                        print(f"✅ Deleted: {public_id}")
                        deleted_count += 1
                    else:
                        print(f"⚠️ Failed to delete: {public_id}")
                except Exception as e:
                    print(f"❌ Error deleting {public_id}: {str(e)}")
            
            print(f"🗑️  Total deleted: {deleted_count} videos")
            return deleted_count
            
        except Exception as e:
            print(f"❌ Error in delete_all_service_videos: {str(e)}")
            return 0

    @staticmethod
    def upload_service_video(video_path, service_id, format_type='webm'):
        """Upload service animation video to Cloudinary with overwrite"""
        try:
            CloudinaryManager.configure()
            
            if not os.path.exists(video_path):
                print(f"❌ File not found: {video_path}")
                return None
            
            print(f"📤 Uploading {service_id}.{format_type}...")
            
            result = cloudinary.uploader.upload(
                video_path,
                resource_type="video",
                folder="shout-otb/service-animations",
                public_id=f"{service_id}",
                overwrite=True,  # This ensures replacement
                invalidate=True,  # Invalidate CDN cache
                chunk_size=6000000,
                transformation=[
                    {'quality': 'auto:good'},
                    {'format': format_type}
                ]
            )
            
            print(f"✅ Uploaded {service_id}.{format_type}: {result['secure_url']}")
            return result['secure_url']
            
        except Exception as e:
            print(f"❌ Error uploading {service_id}.{format_type}: {str(e)}")
            return None

    @staticmethod
    def upload_all_service_videos(videos_folder='static/videos/', cleanup_first=True):
        """Upload all service animation videos with optional cleanup first"""
        CloudinaryManager.configure()
        
        # Optionally delete all existing videos first
        if cleanup_first:
            CloudinaryManager.delete_all_service_videos()
        
        video_urls = {}
        
        # Map of service IDs to video filenames
        service_video_map = {
            'creative-content': 'creative-content-animation',
            'social-growth': 'social-growth-animation',
            'performance-marketing': 'performance-marketing-animation',
            'web-development': 'web-development-animation',
            'ai-solutions': 'ai-solutions-animation',
            'ecommerce': 'ecommerce-animation',
            'whatsapp-marketing': 'whatsapp-marketing-animation',
            'design': 'design-animation',
            'video-editing': 'video-editing-animation',
            'graphic-design': 'graphic-design-animation',
            'influencer-marketing': 'influencer-marketing-animation',
            'cro-analytics': 'cro-analytics-animation',
            'ugc-creator': 'ugc-creator-animation',
            'ai-content': 'ai-content-animation',
            'ai-automations': 'ai-automations-animation',
            'content-protection': 'content-protection-animation'
        }
        
        for service_id, video_base_name in service_video_map.items():
            print(f"\n🔄 Processing {service_id}...")
            
            # Try WebM first (better compression), then MP4
            webm_path = os.path.join(videos_folder, f"{video_base_name}.webm")
            mp4_path = os.path.join(videos_folder, f"{video_base_name}.mp4")
            
            video_url = None
            if os.path.exists(webm_path):
                video_url = CloudinaryManager.upload_service_video(webm_path, service_id, 'webm')
            elif os.path.exists(mp4_path):
                video_url = CloudinaryManager.upload_service_video(mp4_path, service_id, 'mp4')
            
            if video_url:
                video_urls[service_id] = video_url
            else:
                print(f"⚠️ No video found for {service_id}")
        
        return video_urls

    @staticmethod
    def update_service_data_file(video_urls, output_file='data/service_data.py'):
        """Smart update: Only replace SERVICE_VIDEOS section while preserving SERVICE_DATA"""
        try:
            # Read the existing service_data.py to preserve all content
            if not os.path.exists(output_file):
                print(f"❌ File not found: {output_file}")
                return False
            
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create the new SERVICE_VIDEOS content
            new_videos_section = "SERVICE_VIDEOS = {\n"
            
            for service_id, url in video_urls.items():
                new_videos_section += f"    '{service_id}': '{url}',\n"
            
            # Add services without videos as None
            all_services = [
                'creative-content', 'social-growth', 'performance-marketing', 
                'web-development', 'ai-solutions', 'ecommerce', 'whatsapp-marketing',
                'design', 'video-editing', 'graphic-design', 'influencer-marketing',
                'cro-analytics', 'ugc-creator', 'ai-content', 'ai-automations', 
                'content-protection'
            ]
            
            for service_id in all_services:
                if service_id not in video_urls:
                    new_videos_section += f"    '{service_id}': None,\n"
            
            new_videos_section += "}\n\n"
            new_videos_section += "# Add a default video for services without custom animations\n"
            new_videos_section += "DEFAULT_SERVICE_VIDEO = 'https://res.cloudinary.com/deuqi5d71/video/upload/v1763390453/shout-otb/service-animations/creative-content.webm'\n"
            
            # Use regex to replace only the SERVICE_VIDEOS section
            # Pattern to match from SERVICE_VIDEOS to the end of DEFAULT_SERVICE_VIDEO
            pattern = r"SERVICE_VIDEOS\s*=\s*\{[^}]+\}(?:\s*\n\s*# Add a default video[^\n]+\n\s*DEFAULT_SERVICE_VIDEO[^\n]+)?"
            
            if re.search(pattern, content, re.DOTALL):
                # Replace existing SERVICE_VIDEOS section
                new_content = re.sub(pattern, new_videos_section, content, flags=re.DOTALL)
                print("✅ Replaced existing SERVICE_VIDEOS section")
            else:
                # SERVICE_VIDEOS section doesn't exist, append it at the end
                new_content = content.rstrip() + "\n\n" + new_videos_section
                print("✅ Added new SERVICE_VIDEOS section")
            
            # Write the updated file back
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ Updated {output_file} with {len(video_urls)} video URLs")
            print("✅ Preserved all SERVICE_DATA and other content")
            return True
            
        except Exception as e:
            print(f"❌ Error updating service_data.py: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def backup_service_data_file(original_file='data/service_data.py'):
        """Create a backup of the service_data.py file before making changes"""
        try:
            if not os.path.exists(original_file):
                return False
            
            import shutil
            from datetime import datetime
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"data/service_data_backup_{timestamp}.py"
            
            # Copy the file
            shutil.copy2(original_file, backup_file)
            print(f"💾 Backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            print(f"⚠️ Could not create backup: {str(e)}")
            return False

    @staticmethod
    def list_uploaded_videos():
        """List all uploaded service videos for verification"""
        try:
            CloudinaryManager.configure()
            
            result = cloudinary.api.resources(
                type="upload",
                resource_type="video",
                prefix="shout-otb/service-animations",
                max_results=100
            )
            
            videos = []
            for resource in result.get('resources', []):
                videos.append({
                    'public_id': resource['public_id'],
                    'url': resource['secure_url'],
                    'format': resource['format'],
                    'size': resource['bytes']
                })
            
            return videos
        except Exception as e:
            print(f"Error listing videos: {str(e)}")
            return []