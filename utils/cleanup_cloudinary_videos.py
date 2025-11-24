# cleanup_cloudinary_videos.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = '.env'
if os.path.exists(env_path):
    load_dotenv(env_path)
    print("✅ Loaded .env file")

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from cloudinary_manager import CloudinaryManager

def main():
    print("🗑️  Cloudinary Video Cleanup Tool")
    print("⚠️  This will delete ALL service videos from Cloudinary!")
    
    # Test connection
    if not CloudinaryManager.test_connection():
        print("❌ Cloudinary connection failed.")
        return
    
    # Ask for confirmation
    confirmation = input("\nType 'DELETE ALL' to confirm: ")
    if confirmation != 'DELETE ALL':
        print("❌ Cleanup cancelled.")
        return
    
    # Delete all videos
    deleted_count = CloudinaryManager.delete_all_service_videos()
    print(f"\n🗑️  Cleanup complete! Deleted {deleted_count} videos.")

if __name__ == "__main__":
    main()