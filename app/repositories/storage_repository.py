from firebase_admin import storage


from firebase_admin import storage

def list_files(prefix: str) -> list[str]:
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix=prefix)
    urls = []
    
    for blob in blobs:
        if blob.name.endswith("/"):
            continue
            
        url = f"https://storage.googleapis.com/{bucket.name}/{blob.name}"
        urls.append(url)
            
    return urls