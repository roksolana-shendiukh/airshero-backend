from firebase_admin import storage


def list_files(prefix: str) -> list[str]:
    bucket = storage.bucket()
    blobs = list(bucket.list_blobs(prefix=prefix))
    urls = []
    
    for blob in blobs:
        if blob.name.endswith("/"):
            continue
            
        try:
            blob.make_public() 
            urls.append(blob.public_url)
        except Exception as e:
            print(f"Error making blob public: {e}")
            
    return urls