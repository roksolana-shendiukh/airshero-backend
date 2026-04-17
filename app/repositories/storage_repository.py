from firebase_admin import storage


from firebase_admin import storage

def list_files(prefix: str) -> list[str]:
    bucket = storage.bucket()
    blobs  = bucket.list_blobs(prefix=prefix)
    urls   = []
    
    for blob in blobs:
        if blob.name.endswith("/"):
            continue
        encoded = blob.name.replace("/", "%2F")
        url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded}?alt=media"
        urls.append(url)
    
    return urls




