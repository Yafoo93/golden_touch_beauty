# Cloudflare R2 media storage

Golden Touch uses separate Cloudflare R2 buckets so public catalogue images
and confidential customer files never share the same access policy.

## Storage boundary

- `public_media`: product, service, and approved gallery images. URLs use the
  public R2 hostname and do not contain credentials.
- `private_media`: booking treatment/intake photographs and future sensitive
  records. Objects remain private and URLs are signed with a short expiry.
- `default`: deliberately points to private storage. Every new public upload
  field must explicitly opt into `public_media`.
- Automated tests always use local disposable storage and never contact R2.

## Backend environment variables

Configure these in `backend/.env` locally and in the Render backend service:

```text
USE_R2_STORAGE=True
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_PUBLIC_BUCKET=golden-touch-public-media
R2_PUBLIC_ACCESS_KEY_ID=<public-bucket-token-id>
R2_PUBLIC_SECRET_ACCESS_KEY=<public-bucket-token-secret>
R2_PUBLIC_CUSTOM_DOMAIN=<public-hostname-without-https>
R2_PRIVATE_BUCKET=golden-touch-private-media
R2_PRIVATE_ACCESS_KEY_ID=<private-bucket-token-id>
R2_PRIVATE_SECRET_ACCESS_KEY=<private-bucket-token-secret>
R2_PRIVATE_URL_EXPIRY=300
```

Do not add `/` to bucket names or include `https://` in
`R2_PUBLIC_CUSTOM_DOMAIN`. Never commit either access key.

## Frontend environment variable

Configure this in `frontend/.env.local` and in the Render frontend service:

```text
NEXT_PUBLIC_MEDIA_URL=https://<public-media-hostname>
```

Redeploy the frontend after changing this build-time variable. Replace the
development `r2.dev` hostname with the future media custom domain before the
production launch.

## Verification

Run these commands from `backend`:

```powershell
python manage.py check
python manage.py check_r2_storage
```

The second command uploads, reads, and deletes one diagnostic object in each
bucket. It prints only pass/fail results and never prints credentials or signed
private URLs.

## Deployment

1. Add `django-storages[s3]` dependencies by deploying `requirements.txt`.
2. Add all backend variables above to Render.
3. Add `NEXT_PUBLIC_MEDIA_URL` to the Render frontend service.
4. Deploy the backend so the storage-field migrations run.
5. Deploy the frontend.
6. Run `python manage.py check_r2_storage` from an authorized environment.
7. Upload a test product image and confirm its public URL loads.
8. Upload a test booking photo and confirm the bucket is not publicly browsable.

Existing files are not copied merely by changing the Django storage backend.
Any media that existed only on a local or ephemeral Render disk must be uploaded
to its correct bucket separately; its object key must continue to match the
file name stored in PostgreSQL.
