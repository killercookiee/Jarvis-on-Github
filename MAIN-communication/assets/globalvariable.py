import threading
import copy

class GlobalVariable:
    def __init__(self, value):
        """Wraps any object (dict, list, tuple) to make it thread-safe."""
        self._lock = threading.RLock()
        self._set_value(value)

    def _set_value(self, value):
        """Detects the object type and initializes storage."""
        if isinstance(value, dict):
            self._type = "dict"
        elif isinstance(value, list):
            self._type = "list"
        elif isinstance(value, tuple):
            self._type = "tuple"
        else:
            raise TypeError(f"GlobalVariable only supports dict, list, or tuple, not {type(value)}")
        self._value = value

    ## === THREAD-SAFE DICTIONARY OPERATIONS === ##

    def keys(self):
        """Thread-safe dict.keys()"""
        if self._type != "dict":
            raise AttributeError("keys() is only available for dicts")
        with self._lock:
            return list(self._value.keys())

    def values(self):
        """Thread-safe dict.values()"""
        if self._type != "dict":
            raise AttributeError("values() is only available for dicts")
        with self._lock:
            return list(self._value.values())

    def items(self):
        """Thread-safe dict.items()"""
        if self._type != "dict":
            raise AttributeError("items() is only available for dicts")
        with self._lock:
            return list(self._value.items())

    def get(self, key, default=None):
        """Thread-safe dict.get() with full safe nested lookups."""
        if self._type != "dict":
            raise AttributeError("get() is only available for dicts")
        with self._lock:
            value = self._value.get(key, default)
            if value is None:
                return GlobalVariable({})
            if isinstance(value, dict):
                return GlobalVariable(value)
            return value

    def setdefault(self, key, default=None):
        """Thread-safe dict.setdefault()"""
        if self._type != "dict":
            raise AttributeError("setdefault() is only available for dicts")
        with self._lock:
            return self._value.setdefault(key, default)

    def pop(self, key, default=None):
        """Thread-safe dict.pop()"""
        if self._type != "dict":
            raise AttributeError("pop() is only available for dicts")
        with self._lock:
            return self._value.pop(key, default)

    def popitem(self):
        """Thread-safe dict.popitem()"""
        if self._type != "dict":
            raise AttributeError("popitem() is only available for dicts")
        with self._lock:
            return self._value.popitem()

    def copy(self):
        """Thread-safe dict.copy()"""
        if self._type != "dict":
            raise AttributeError("copy() is only available for dicts")
        with self._lock:
            return self._value.copy()

    ## === GENERAL DICT/LIST METHODS === ##
    def __getitem__(self, key):
        with self._lock:
            return self._value.get(key, None)

    def __setitem__(self, key, value):
        with self._lock:
            self._value[key] = value

    def __delitem__(self, key):
        with self._lock:
            del self._value[key]

    def __contains__(self, item):
        with self._lock:
            return item in self._value

    def __iter__(self):
        with self._lock:
            return iter(copy.deepcopy(self._value))

    def __len__(self):
        with self._lock:
            return len(self._value)

    def update(self, other_dict):
        """Thread-safe dict.update()"""
        if self._type != "dict":
            raise AttributeError("update() is only available for dicts")
        with self._lock:
            self._value.update(other_dict)

    ## === SNAPSHOT FUNCTION === ##
    def snapshot(self):
        """Returns a deep copy to prevent race conditions."""
        with self._lock:
            return copy.deepcopy(self._value)

    def __repr__(self):
        with self._lock:
            return repr(self._value)
