"""Named file-storage selectors used by model fields.

The callables are migration-safe and defer resolving Django's storage aliases
until the active settings profile has been loaded. Production maps these
aliases to separate Cloudflare R2 buckets; local development maps both to the
local media directory.
"""

from django.core.files.storage import storages


def public_media_storage():
    return storages["public_media"]


def private_media_storage():
    return storages["private_media"]
