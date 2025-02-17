from functools import wraps
import time
from sanic.response import json

class RateLimiter:
    def __init__(self):
        self.storage = {}

    
    async def limit(self, calls, per_second, func, request, *args, **kwargs):

        current_time = time.time()
        cell = self.storage.get(request.ip)

        if not cell:
            cell = [calls-1, current_time]
            self.storage[request.ip] = cell
            return await func(request,*args,**kwargs)

        time_delta = current_time - cell[-1]
        to_add = int(time_delta*(calls/per_second))
        cell[0] += to_add

        if cell[0] > calls:
            cell[0] = calls
                    
        if cell[0] <= 0:
            return json({"success": False, "ratelimit": True})

        self.storage[request.ip][0] -= 1
        self.storage[request.ip][1] = current_time
        return await func(request, *args, **kwargs)


class EndpointLimiter:
    def __init__(self):
        self.funcs = {}


    def limit(self, calls, per_second):
        def decorator(func):
            @wraps(func)
            async def wrapper(request, *args, **kwargs):
                try:
                    return await self.funcs[func.__name__].limit(calls, per_second, func, request, *args, **kwargs)
                except KeyError:
                    rate_limiter = RateLimiter()
                    self.funcs[func.__name__] = rate_limiter
                    return await self.funcs[func.__name__].limit(calls, per_second, func, request, *args, **kwargs)
            return wrapper
        return decorator
