# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

import redis
from config import REDIS_URL

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
