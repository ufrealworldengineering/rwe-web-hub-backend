import os
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Use Service Role Key for backend operations
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
RESUME_BUCKET = "resumes"

supabase_storage: Client = create_client(URL, KEY)

def initialize_storage():
    """Run this once (or in main.py startup) to ensure the bucket exists."""
    try:
        supabase_storage.storage.create_bucket(
            RESUME_BUCKET,
            options={
                "public": True, 
                "allowed_mime_types": ["application/pdf"],
                "file_size_limit": 5242880 # 5MB limit is plenty for PDFs
            }
        )
        print(f"✅ Bucket '{RESUME_BUCKET}' ready.")
    except Exception as e:
        if "already exists" not in str(e).lower():
            print(f"❌ Storage Error: {e}")

async def upload_resume(file_content: bytes, original_filename: str) -> str:
    """Uploads and returns the full public URL."""
    ext = original_filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"
    path = f"applications/{unique_name}" # Organizing into a subfolder

    supabase_storage.storage.from_(RESUME_BUCKET).upload(
        path=path,
        file=file_content,
        file_options={"content-type": "application/pdf"}
    )
    
    # Generate the public URL to store in the DB
    res = supabase_storage.storage.from_(RESUME_BUCKET).get_public_url(path)
    return res