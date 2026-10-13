"""Validated optional widget defaults for a shareable calculation URL."""
import math
import datetime


class SharedInputs:
    def __init__(self, params):
        self.params = params if params.get("prefill") == "1" else {}
        self.errors = []

    def text(self, name, default=""):
        value = self.params.get(name, default)
        if not isinstance(value, str) or len(value) > 200 or any(ord(c) < 32 for c in value):
            self.errors.append(name)
            return default
        return value

    def number(self, name, default, minimum=0, maximum=1_000_000_000, integer=False):
        if name not in self.params:
            return default
        try:
            value = float(self.params[name])
            if not math.isfinite(value) or not minimum <= value <= maximum or (integer and not value.is_integer()):
                raise ValueError("Invalid shared value")
            return int(value) if integer else value
        except (ValueError, TypeError, OverflowError):
            self.errors.append(name)
            return default

    def index(self, name, options, default=0):
        if name not in self.params:
            return default
        value = self.params[name]
        if value not in options:
            self.errors.append(name)
            return default
        return options.index(value)

    def date(self, name, default):
        if name not in self.params:
            return default
        try:
            value = datetime.date.fromisoformat(self.params[name])
            if not datetime.date(2000, 1, 1) <= value <= datetime.date(2100, 12, 31):
                raise ValueError("Date out of range")
            return value
        except (TypeError, ValueError):
            self.errors.append(name)
            return default
