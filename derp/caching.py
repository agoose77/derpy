from functools import wraps, update_wrapper

cache_dict_type = dict


def memoized(func):
    """Weakly memoized function accepting 0 non-self args"""
    memo = cache_dict_type()

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
    memo = cache_dict_type()

    @wraps(func)
    def wrapper(self, *args, memo=memo):
        try:
            result = memo[self, args]
        except KeyError:
            result = memo[self, args] = func.__get__(self)(*args)
        return result

    return wrapper


def fixed_point(func):
    """Compute the fixed point of a function F accepting no args"""
    memo = cache_dict_type()

    @wraps(func)
    def wrapper(self, memo=memo):
        try:
            return memo[self]
        except KeyError:
            memo[self] = self
            result = memo[self] = func.__get__(self)()
            return result

    return wrapper


class _CachedProperty:
    """Cached property descriptor"""

    def __init__(self, func):
        self._func = func
        self._cache = cache_dict_type()
        update_wrapper(self, func)

    def clear_cache(self):
        self._cache.clear()

    def __get__(self, instance, cls):
        try:
            return self._cache[instance]
        except KeyError:
            self._cache[instance] = result = self._func.__get__(instance, cls)()
            return result


cached_property = _CachedProperty
