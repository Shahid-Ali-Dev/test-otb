# upload_service_videos.py - SMART VERSION (Preserves all data)
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
env_path = '.env'
if os.path.exists(env_path):
    load_dotenv(env_path)
    print("✅ Loaded .env file")
else:
    print("❌ .env file not found - checking system environment variables")

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from cloudinary_manager import CloudinaryManager

def main():
    print("🚀 Starting Service Videos Upload to Cloudinary...")
    print("🔄 This will REPLACE all existing videos and update ONLY SERVICE_VIDEOS in service_data.py")
    print("💾 All SERVICE_DATA and other content will be preserved")
    print(f"📁 Current directory: {os.getcwd()}")
    
    # Debug: Show Cloudinary config
    print("\n🔧 Cloudinary Configuration:")
    print(f"   Cloud Name: {os.environ.get('CLOUDINARY_CLOUD_NAME', 'NOT SET')}")
    print(f"   API Key: {os.environ.get('CLOUDINARY_API_KEY', 'NOT SET')}")
    print(f"   API Secret: {'SET' if os.environ.get('CLOUDINARY_API_SECRET') else 'NOT SET'}")
    
    # Test connection first
    print("\n🔌 Testing Cloudinary connection...")
    if not CloudinaryManager.test_connection():
        print("❌ Cloudinary connection failed. Check your credentials.")
        print("\n💡 Troubleshooting steps:")
        print("   1. Make sure .env file is in the same directory as this script")
        print("   2. Check that Cloudinary credentials are correct in .env file")
        print("   3. Ensure .env file has no spaces around the = signs")
        return
    
    # Check if videos folder exists
    videos_folder = 'static/videos/'
    if not os.path.exists(videos_folder):
        print(f"❌ Videos folder not found: {videos_folder}")
        print("💡 Please make sure your videos are in static/videos/")
        return
    
    print(f"📁 Found videos folder: {videos_folder}")
    
    # Check if service_data.py exists
    service_data_file = 'data/service_data.py'
    if not os.path.exists(service_data_file):
        print(f"❌ Service data file not found: {service_data_file}")
        print("💡 Please make sure your service_data.py is in the data/ folder")
        return
    
    print(f"📁 Found service data file: {service_data_file}")
    
    # List available videos
    print("\n📹 Checking available videos...")
    video_files = [f for f in os.listdir(videos_folder) if f.endswith(('.webm', '.mp4', '.mkv'))]
    print(f"Found {len(video_files)} video files:")
    for file in video_files:
        file_path = os.path.join(videos_folder, file)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        print(f"   - {file} ({file_size:.1f} MB)")
    
    if not video_files:
        print("❌ No video files found in the videos folder!")
        return
    
    # Create backup first
    print("\n💾 Creating backup of service_data.py...")
    backup_file = CloudinaryManager.backup_service_data_file(service_data_file)
    if backup_file:
        print(f"✅ Backup created: {backup_file}")
    
    # Ask for confirmation
    print("\n⚠️  WARNING: This will:")
    print("   - Delete ALL existing videos in Cloudinary")
    print("   - Upload new videos")
    print("   - Update ONLY the SERVICE_VIDEOS section in service_data.py")
    print("   - Preserve ALL your SERVICE_DATA and other content")
    
    confirmation = input("\n   Type 'YES' to continue: ")
    if confirmation != 'YES':
        print("❌ Upload cancelled.")
        return
    
    # Upload all videos (with cleanup first)
    print("\n⬆️ Starting upload process...")
    video_urls = CloudinaryManager.upload_all_service_videos(
        videos_folder, 
        cleanup_first=True  # This ensures old videos are deleted first
    )
    
    print("\n📊 Upload Summary:")
    print(f"✅ Successfully uploaded: {len(video_urls)} videos")
    
    if video_urls:
        # Update service_data.py automatically (only SERVICE_VIDEOS section)
        print("\n📝 Smart-updating service_data.py (preserving SERVICE_DATA)...")
        success = CloudinaryManager.update_service_data_file(video_urls, service_data_file)
        
        if success:
            print("✅ service_data.py updated successfully!")
            print("✅ All SERVICE_DATA preserved intact!")
            
            # Show the updated URLs
            print("\n🔗 Updated SERVICE_VIDEOS in service_data.py:")
            print("SERVICE_VIDEOS = {")
            for service_id, url in video_urls.items():
                print(f"    '{service_id}': '{url}',")
            for service_id in ['social-growth', 'performance-marketing', 'ai-solutions', 
                             'ecommerce', 'whatsapp-marketing', 'influencer-marketing', 
                             'cro-analytics', 'ugc-creator', 'ai-content', 'content-protection']:
                if service_id not in video_urls:
                    print(f"    '{service_id}': None,")
            print("}")
        else:
            print("❌ Failed to update service_data.py")
            if backup_file:
                print(f"💾 Your original data is safe in: {backup_file}")
        
        # Save to a separate backup file for reference
        with open('cloudinary_video_urls_backup.py', 'w') as f:
            f.write("# Backup of Cloudinary video URLs - for reference only\n")
            f.write("SERVICE_VIDEOS = {\n")
            for service_id, url in video_urls.items():
                f.write(f"    '{service_id}': '{url}',\n")
            f.write("}\n")
        
        print("\n💾 Video URLs backup saved to 'cloudinary_video_urls_backup.py'")
        
        # List uploaded videos for verification
        print("\n🔍 Verifying uploaded videos...")
        uploaded_videos = CloudinaryManager.list_uploaded_videos()
        print(f"📹 Found {len(uploaded_videos)} videos in Cloudinary:")
        for video in uploaded_videos:
            print(f"   - {video['public_id']} ({video['format']})")
            
        print(f"\n🎉 Upload complete! Your service_data.py has been smart-updated.")
        print("💡 SERVICE_DATA preserved, only SERVICE_VIDEOS section was updated.")
        print("💡 You may need to restart your Flask app for changes to take effect.")
        
    else:
        print("❌ No videos were uploaded. Please check the errors above.")
        if backup_file:
            print(f"💾 Your original data is safe in: {backup_file}")

if __name__ == "__main__":
    main()