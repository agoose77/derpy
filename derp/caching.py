from functools import wraps, update_wrapper


_cache_dict_type = dict
_root_caches = []


def create_cache():
    memo = _cache_dict_type()
    _root_caches.append(memo)
    return memo


def clear_caches():
    for cache in _root_caches:
        cache.clear()



def memoized(func):
    """Weakly memoized function accepting 0 non-self args"""
    memo = create_cache()

    @wraps(func)
    def wrapper(self, memo=memo):
        try:
            return memo[self]
        except KeyError:
            result = memo[self] = func.__get__(self)()
            return result

    return wrapper


def memoized_n(func):
    """Memoized function accepting self and *args"""
    memo = create_cache()

    @wraps(func)
    def wrapper(self, *args, memo=memo, func=func):
        try:
            return memo[self, args]
        except KeyError:
            result = memo[self, args] = func.__get__(self)(*args)
            return result

    return wrapper


def recursive_memoize(func):
    """Compute the fixed point of a function F accepting no args"""
    memo = create_cache()

    @wraps(func)
    def wrapper(self, memo=memo):
        try:
            return memo[self]
        except KeyError:
            memo[self] = self
            result = memo[self] = func.__get__(self)()
            return result

    return wrapper


def cached_property(func):
    memo = create_cache()

    @property
    @wraps(func)
    def wrapper(self):
        try:
            return memo[self]
        except KeyError:
            result = memo[self] = func.__get__(self)()
            return result
    return wrapper
