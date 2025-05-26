import redis

class CacheHandler:
    def __init__(self, redis_url):
        self.redis = redis.from_url(redis_url)

    def set(self, key, value, expire=None):
        self.redis.set(key, value, ex=expire)

    def get(self, key):
        return self.redis.get(key)

    def delete(self, key):
        self.redis.delete(key) 