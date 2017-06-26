import asyncio


class RWLock:
    def __init__(self):
        self.cond = asyncio.Condition()
        self.readers = 0
        self.writer = False

    async def lock(self, write=False):
        async with self.cond:
            while self.readers and write or self.writer:
                await self.cond.wait()
            if write: self.writer = True
            else: self.readers += 1
            print("locked for write" if write else "locked for read")

    async def unlock(self):
        async with self.cond:
            if self.writer: self.writer = False
            else: self.readers -= 1
            self.cond.notify_all()


def test_rwlock():
    import random
    holders = set()
    lock = RWLock()

    def invariant():
        if any(r.startswith("w-") for r in holders):
            # Either there's a single writer
            assert len(holders) == 1
            assert all(r.startswith("w-") for r in holders)
        else:
            # Or unlimited number of readers
            assert all(r.startswith("r-") for r in holders)

    async def reader():
        await asyncio.sleep(random.random() / 10)
        self = object()
        invariant()
        await lock.lock()
        holders.add(f"r-{id(self)}")
        await asyncio.sleep(random.random() / 10)
        invariant()
        holders.remove(f"r-{id(self)}")
        await lock.unlock()
        invariant()

    async def writer():
        await asyncio.sleep(random.random() / 10)
        self = object()
        invariant()
        await lock.lock(write=True)
        holders.add(f"w-{id(self)}")
        await asyncio.sleep(random.random() / 10)
        invariant()
        holders.remove(f"w-{id(self)}")
        await lock.unlock()
        invariant()

    async def test():
        assert not lock.readers and not lock.writer
        tasks = set()
        for i in range(100):
            await asyncio.sleep(random.random() / 30)
            tasks.add(asyncio.ensure_future(writer() if random.random() < 0.10 else reader()))

        await asyncio.gather(*tasks)
        assert not lock.readers and not lock.writer

    print("----")
    asyncio.get_event_loop().run_until_complete(test())

    print("----")
    asyncio.get_event_loop().run_until_complete(test())


if __name__ == "__main__":
    test_rwlock()
