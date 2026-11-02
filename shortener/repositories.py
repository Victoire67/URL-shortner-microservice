import redis


class RedisUrlRepository:
    """Save and reads short code Long URL paris in Redis ---> """

    KEY_PREFIX = "url:"

    def __init__(self, client: redis.Redis):
        self._client = client

    def save_if_absent(self, short_code: str, long_url: str) -> bool:
        key = f"{self.KEY_PREFIX}{short_code}"
        return bool(self._client.set(key, long_url, nx=True))

    def get(self , short_code : str) -> str | None : 
        key = f"{self.KEY_PREFIX}{short_code}"
        return self._client.get(key)

    