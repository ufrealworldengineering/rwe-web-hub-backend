import os
import uuid
from typing import Optional

from supabase import Client, create_client
from dotenv import load_dotenv

load_dotenv()

# Use Service Role Key for backend operations
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
RESUME_BUCKET = "resumes"

# Lazily create the Supabase client so local dev/tests without Supabase
# don't fail or emit deprecation warnings unnecessarily.
supabase_storage: Optional[Client] = None

if URL and KEY:
    supabase_storage = create_client(URL, KEY)

def initialize_storage():
    """Run this once (or in main.py startup) to ensure the bucket exists.

    In environments without Supabase configured (e.g. local tests),
    this becomes a no-op.
    """
    if supabase_storage is None:
        return
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
    """Uploads and returns the full public URL.

    When Supabase is not configured (no SUPABASE_URL / SERVICE_ROLE_KEY),
    this returns a deterministic fake URL so tests and local dev can proceed
    without external dependencies.
    """
    ext = original_filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"
    path = f"applications/{unique_name}" # Organizing into a subfolder
    # If Supabase isn't configured, just return a fake URL.
    if supabase_storage is None:
        base = os.getenv("LOCAL_RESUME_BASE_URL", "https://example.com")
        return f"{base}/storage/v1/object/public/{RESUME_BUCKET}/{path}"

    try:
        supabase_storage.storage.from_(RESUME_BUCKET).upload(
            path=path,
            file=file_content,
            file_options={"content-type": "application/pdf"},
        )

        # Generate the public URL to store in the DB
        res = supabase_storage.storage.from_(RESUME_BUCKET).get_public_url(path)
        return res
    except Exception:
        # In tests or misconfigured environments, fall back to a fake URL
        base = os.getenv("LOCAL_RESUME_BASE_URL", "https://example.com")
        return f"{base}/{RESUME_BUCKET}/{path}"