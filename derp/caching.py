cache_dict_type = dict


def weakly_memoized(f):
    """Weakly memoized function accepting 0 non-self args"""
    memo = cache_dict_type()

    def wrapper(self, memo=memo):
        try:
            return memo[self]

        except KeyError:
            result = memo[self] = f.__get__(self)()
            return result

    return wrapper


def weakly_memoized_n(f):
    """Weakly memoized function accepting self and *args"""
    memo = cache_dict_type()

    def wrapper(self, *args, memo=memo):
        try:
            self_memo = memo[self]
        except KeyError:
            self_memo = memo[self] = {}

        try:
            result = self_memo[args]
        except KeyError:
            result = self_memo[args] = f.__get__(self)(*args)
        return result

    return wrapper

weakly_memoized = weakly_memoized_n

def fixed_point(f):
    memo = cache_dict_type()

    def wrapper(self, memo=memo):
        try:
            return memo[self]
        except KeyError:
            memo[self] = self
            result = memo[self] = f.__get__(self)()
            return result

    return wrapper


class _CachedProperty:
    """Cached property descriptor"""

    def __init__(self, func):
        self._func = func
        self._cache = cache_dict_type()

    def clear_cache(self):
        self._cache.clear()

    def __get__(self, instance, cls):
        try:
            return self._cache[instance]
        except KeyError:
            self._cache[instance] = result = self._func.__get__(instance, cls)()
            return result

cached_property = _CachedProperty