import tempfile
import unittest
from pathlib import Path

from invisible_inn.engine import GameState
from invisible_inn.storage import ABANDONED, ACTIVE, FINISHED, Storage


class StorageTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db = Storage(Path(self._tmp.name) / "sub" / "test.db")
        await self.db.setup()

    async def asyncTearDown(self):
        self._tmp.cleanup()

    async def make(self, user=1, guild=10, thread=100):
        return await self.db.create_session(
            guild_id=guild, channel_id=50, thread_id=thread, owner_id=user,
            story_id="invisible_inn", state=GameState("arrival"),
        )

    async def test_setup_is_repeatable(self):
        await self.db.setup()  # migrations must not re-run

    async def test_create_and_fetch(self):
        s = await self.make()
        self.assertEqual(s.status, ACTIVE)
        self.assertEqual((await self.db.get_session(s.id)).state.scene_id, "arrival")
        self.assertEqual((await self.db.get_session_by_thread(100)).id, s.id)

    async def test_owner_is_a_player(self):
        s = await self.make(user=7)
        self.assertTrue(await self.db.is_player(s.id, 7))
        self.assertFalse(await self.db.is_player(s.id, 8))
        await self.db.add_player(s.id, 8)
        self.assertTrue(await self.db.is_player(s.id, 8))

    async def test_active_session_lookup(self):
        s = await self.make(user=7)
        self.assertEqual((await self.db.active_session_for_user(10, 7)).id, s.id)
        self.assertIsNone(await self.db.active_session_for_user(11, 7), "other server")
        await self.db.set_status(s.id, ABANDONED)
        self.assertIsNone(await self.db.active_session_for_user(10, 7))

    async def test_save_state(self):
        s = await self.make()
        await self.db.save_state(s.id, GameState("foyer", turn=1, inventory=["brass_key"]), FINISHED)
        loaded = await self.db.get_session(s.id)
        self.assertEqual(loaded.state.inventory, ["brass_key"])
        self.assertEqual(loaded.status, FINISHED)


if __name__ == "__main__":
    unittest.main()
