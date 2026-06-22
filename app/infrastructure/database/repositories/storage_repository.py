from firebase_admin import storage


from firebase_admin import storage

def list_files(prefix: str) -> list[str]:
    bucket = storage.bucket()
    blobs  = bucket.list_blobs(prefix=prefix)
    urls   = []
    
    for blob in blobs:
        if blob.name.endswith("/"):
            continue
        import urllib.parse
        encoded = urllib.parse.quote(blob.name, safe='')
        url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded}?alt=media"
        urls.append(url)
    
    return urls




