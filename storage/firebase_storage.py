"""
Firebase Storage
Handles uploading extracted data and metadata to Firebase cloud storage
for persistent access and collaboration.
"""

import os

try:
    import firebase_admin
    from firebase_admin import credentials, storage
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False


def initialize_firebase(service_account_path=None, storage_bucket=None):
    """
    Initialize Firebase with service account credentials.
    
    Args:
        service_account_path: Path to service account JSON (from env if not provided)
        storage_bucket: Firebase storage bucket name (from env if not provided)
    
    Returns:
        Firebase storage bucket object
    """
    if not FIREBASE_AVAILABLE:
        raise ImportError("firebase-admin required: pip install firebase-admin")
    
    if service_account_path is None:
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
    if storage_bucket is None:
        storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "")
    
    if not firebase_admin._apps:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})
    
    return storage.bucket()


def upload_file(local_path, remote_path, bucket=None):
    """
    Upload a file to Firebase storage.
    
    Args:
        local_path: Path to local file
        remote_path: Destination path in Firebase storage
        bucket: Firebase bucket (initializes if not provided)
    """
    if bucket is None:
        bucket = initialize_firebase()
    
    blob = bucket.blob(remote_path)
    blob.upload_from_filename(local_path)
    print(f"Uploaded: {local_path} → {remote_path}")


def upload_directory(local_dir, remote_prefix, bucket=None):
    """
    Upload all files in a directory to Firebase storage.
    
    Args:
        local_dir: Local directory path
        remote_prefix: Remote path prefix
        bucket: Firebase bucket
    """
    if bucket is None:
        bucket = initialize_firebase()
    
    for filename in os.listdir(local_dir):
        local_path = os.path.join(local_dir, filename)
        if os.path.isfile(local_path):
            remote_path = f"{remote_prefix}/{filename}"
            upload_file(local_path, remote_path, bucket)
