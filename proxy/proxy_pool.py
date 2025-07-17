import redis
# from itertools import cycle

# REDIS_KEY = "tor:proxy_index"
# PROXY_PORTS = [9050, 9052, 9054, 9056, 9058, 9060, 9062, 9064, 9066, 9068]
# PROXIES = [f"socks5h://127.0.0.1:{port}" for port in PROXY_PORTS]

# class ProxyPool:
#     def __init__(self, redis_host="localhost", redis_port=6379):
#         self.redis = redis.Redis(host=redis_host, port=redis_port, db=0)

#     def get_next_proxy(self):
#         index = self.redis.incr(REDIS_KEY) % len(PROXIES)
#         return PROXIES[index]

REDIS_KEY = "tor:proxy_index"
REDIS_PROXY_LIST = "tor:proxy_list"

class ProxyPool:
    def __init__(self, redis_host="localhost", redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=0)

    def init_proxies(self, ports):
        proxies = [f"socks5h://127.0.0.1:{port}" for port in ports]
        self.redis.delete(REDIS_PROXY_LIST)
        self.redis.rpush(REDIS_PROXY_LIST, *proxies)

    def get_next_proxy(self):
        total = self.redis.llen(REDIS_PROXY_LIST)
        index = self.redis.incr(REDIS_KEY) % total
        proxy = self.redis.lindex(REDIS_PROXY_LIST, index)
        return proxy.decode() if proxy else None