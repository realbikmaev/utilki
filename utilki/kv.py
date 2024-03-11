"""
simple key-value store using sqlite3

shamelessly stolen from https://pypi.org/project/kv/
now it's typed + we can add default values
"""

import json
import sqlite3
from collections.abc import MutableMapping
from contextlib import contextmanager
from logging import Logger
from typing import Any
from copy import deepcopy


class KV(MutableMapping[str, Any]):
    def __init__(
        self,
        db: str = ":memory:",
        table: str = "kv",
        default: Any = None,
        timeout: int = 5,
        logger: Logger | None = None,
    ):
        self._db_uri = db
        self._table = table
        self._default = default
        self._logger = logger
        self._db = sqlite3.connect(db, timeout=timeout)
        self._db.isolation_level = None
        self._attr: str = None  # type: ignore
        self._locks = 0
        self._execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table} 
            (key PRIMARY KEY, value)
            """
        )

    def incr(self, key: str, amount: int = 1) -> int:
        with self.lock():
            val = self[key]
            val += amount
            self[key] = val
            return val

    def decr(self, key: str, amount: int = 1) -> int:
        with self.lock():
            val = self[key]
            val -= amount
            self[key] = val
            return val

    def clone(self, table: str) -> "KV":
        return KV(self._db_uri, table)

    def _execute(self, sql: str, params: tuple[str, ...] = ()):
        if params:
            return self._db.cursor().execute(sql, params)
        else:
            return self._db.cursor().execute(sql)

    def __len__(self):
        [[n]] = self._execute(f"SELECT COUNT(*) FROM {self._table}")
        return n

    def __getitem__(self, key: str) -> int:
        if key is None:  # type: ignore
            raise ValueError("key cannot be None")

        for row in self._execute(
            f"""
            SELECT value FROM {self._table} WHERE key=?
            """,
            (key,),
        ):
            result = json.loads(row[0])
            return result
        else:
            if self._default is not None:
                return deepcopy(self._default)
            else:
                raise KeyError

    def __iter__(self):
        return (
            key for [key] in self._execute(f"SELECT key FROM {self._table}")
        )

    def __setitem__(self, key: str, value: Any):
        jvalue = json.dumps(value)
        with self.lock():
            try:
                self._execute(
                    f"INSERT INTO {self._table} VALUES (?, ?)",
                    (key, jvalue),
                )
            except sqlite3.IntegrityError:
                self._execute(
                    f"UPDATE {self._table} SET value=? WHERE key=?",
                    (jvalue, key),
                )

    def __delitem__(self, key: str):
        if key in self:
            self._execute(f"DELETE FROM {self._table} WHERE key=?", (key,))
        else:
            raise KeyError

    @contextmanager
    def lock(self, default: Any = None):
        if not self._locks:
            self._execute("BEGIN IMMEDIATE TRANSACTION")
        self._locks += 1
        previous_default = deepcopy(self._default)
        if default is not None:
            self._default = deepcopy(default)
        try:
            yield self
        finally:
            self._default = deepcopy(previous_default)
            self._locks -= 1
            if not self._locks:
                self._execute("COMMIT")

    def __getattr__(self, name: str) -> "KV":
        self._attr = name
        return self

    def __iadd__(self, other: int):
        if self._attr is None:  # type: ignore
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '_attr'"
            )
        val = self[self._attr]
        val += other
        self[self._attr] = val

    def dict(self):
        return dict(self.items())

    def ratio(
        self,
        of: str,
        over: str,
        eps: float = 1e-8,
        total: bool = False,
        msg: str = "",
    ) -> float:
        if total:
            _ratio = self[of] / (self[of] + self[over] + eps)
            if not msg:
                msg = f"{of}/({of} + {over})"
        else:
            _ratio = self[of] / (self[over] + eps)
            if not msg:
                msg = f"{of}/{over}"
        if self._logger:
            self._logger.info(**{msg: f"{_ratio:.2%}"})  # type: ignore
        return _ratio


if __name__ == "__main__":
    kv = KV(default=0)
    kv["a"] = 1
    kv["b"] = 2
    kv["c"] = 3
    for i in ["a", "b", "c", "d"]:
        print(f"{i}: {kv[i]}")

    e = kv.e
    e += 1
    print(f"e: {kv['e']}")

    kv.f += 1  # type: ignore
    print(f"f: {kv['f']}")
    print(kv.dict())
    print(kv.ratio(of="a", over="b"))
