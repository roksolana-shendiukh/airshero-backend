from firebase_admin import storage


def list_files(prefix: str) -> list[str]:
    bucket = storage.bucket()
    blobs  = list(bucket.list_blobs(prefix=prefix))
    urls   = []
    for blob in blobs:
        if blob.name.endswith("/"):
            continue
        url = blob.generate_signed_url(
            expiration=3600,
            method="GET",
            version="v4",
        )
        urls.append(url)
    return urls