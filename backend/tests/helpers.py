from __future__ import annotations


class FakeScalars:
    def __init__(self, items):
        self._items = list(items)

    def all(self):
        return list(self._items)


class FakeResult:
    def __init__(self, scalar=None, scalars=None):
        self._scalar = scalar
        self._scalars = list(scalars) if scalars is not None else None

    def scalar_one(self):
        return self._scalar

    def scalar_one_or_none(self):
        return self._scalar

    def scalar(self):
        return self._scalar

    def scalars(self):
        return FakeScalars(self._scalars or [])


class FakeDb:
    def __init__(self, execute_results=None, execute_handler=None):
        self.execute_results = list(execute_results or [])
        self.execute_handler = execute_handler
        self.added = []
        self.deleted = []
        self.commits = 0
        self.refreshes = []
        self.flushes = 0

    async def execute(self, query):
        if self.execute_handler is not None:
            return await self.execute_handler(query)
        if not self.execute_results:
            raise AssertionError("Unexpected db.execute() call")
        return self.execute_results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    def add_all(self, items):
        self.added.extend(items)

    async def delete(self, obj):
        self.deleted.append(obj)

    async def commit(self):
        self.commits += 1

    async def refresh(self, obj):
        self.refreshes.append(obj)

    async def flush(self):
        self.flushes += 1
