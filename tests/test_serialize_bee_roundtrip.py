#!/usr/bin/env python3
"""Real (un-mocked) round-trip test for `_serialize_bee`.

The sibling `test_serialize_bee.py` stubs `bee_rpc` entirely, so it can only
assert the *framing* contract — it cannot catch the failure mode Josemi reported
(a packed service whose `.bee` carries block *pointers* without the block
*content*). This test exercises the whole thing against REAL `bee_rpc`, with a
real >10 MiB block, and proves the payload survives a full write -> read cycle
into a *fresh, empty* block directory.

What it guards:
  1. A service with a >= MIN_BUFFER_BLOCK_SIZE file becomes a genuine multiblock
     dir (its `_.json` holds a `[block_id, ...]` pointer, not the bytes).
  2. `_serialize_bee` streams the block *content* into the `.bee` (not just the
     pointer) — the exact thing that was previously unverifiable.
  3. Reading that `.bee` back with an empty BLOCKDIR re-materialises the block
     file and reproduces the original service hash byte-for-byte.

It needs the real nodo deps (`bee_rpc`, `protos`). On a dev box without them
(NODO_DIR not importable) it SKIPS rather than failing, mirroring the lazy-import
contract in `server._serialize_bee`.

Run:  python -m unittest tests.test_serialize_bee_roundtrip   (from repo root)
"""
import hashlib
import json
import os
import sys
import tempfile
import unittest

# Registry/cache/block dirs must exist in the env before `server` is imported,
# matching the module-level contract the other test modules rely on.
_TMP = tempfile.mkdtemp(prefix="packer-bee-rt-")
os.environ.setdefault("CACHE", os.path.join(_TMP, "cache"))
os.environ["BLOCKDIR"] = os.path.join(_TMP, "blocks")
os.makedirs(os.environ["CACHE"], exist_ok=True)
os.makedirs(os.environ["BLOCKDIR"], exist_ok=True)

import server  # noqa: E402

# The real nodo runtime (bee_rpc + protos) lives under NODO_DIR; `_serialize_bee`
# puts it on sys.path lazily. Do the same here so we can build the fixture with
# the real library, and SKIP cleanly when it is not installed.
sys.path.insert(0, server.NODO_DIR)
try:
    from bee_rpc import block_builder  # type: ignore
    from bee_rpc.client import read_from_file  # type: ignore
    from bee_rpc.reader import read_multiblock_directory  # type: ignore
    from bee_rpc.utils import modify_env, Enviroment  # type: ignore
    from protos import celaut_pb2  # type: ignore
    from protos import pack_pb2  # type: ignore

    _HAVE_BEE = True
except Exception:  # noqa: BLE001 - any import failure -> skip, never fail
    _HAVE_BEE = False


def _sha3_of_multiblock(directory: str) -> str:
    """Hash the reconstructed content of a multiblock dir (blocks inlined),
    matching how nodo's integrity check reads a service."""
    h = hashlib.sha3_256()
    for chunk in read_multiblock_directory(directory=directory, ignore_blocks=True):
        if isinstance(chunk, bytes):
            h.update(chunk)
    return h.hexdigest()


@unittest.skipUnless(_HAVE_BEE, "real bee_rpc/protos not available (NODO_DIR)")
class SerializeBeeRoundTrip(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp(prefix="rt-case-")
        self.cache = os.path.join(self.work, "cache")
        self.blocks = os.path.join(self.work, "blocks")
        os.makedirs(self.cache)
        os.makedirs(self.blocks)
        # Point bee_rpc at our sender-side dirs. `_serialize_bee` re-applies the
        # same modify_env from os.environ, so keep env in sync.
        os.environ["CACHE"] = self.cache
        os.environ["BLOCKDIR"] = self.blocks
        modify_env(cache_dir=os.path.abspath(self.cache) + os.sep,
                   block_dir=os.path.abspath(self.blocks) + os.sep)

    def test_block_payload_survives_write_then_read(self):
        # 1. A real >10 MiB block, registered content-addressed in BLOCKDIR.
        payload = os.urandom(11 * 1024 * 1024)
        big = os.path.join(self.work, "big.bin")
        with open(big, "wb") as f:
            f.write(payload)
        block_hash, block = block_builder.create_block(file_path=big, copy=True)
        block_file = os.path.join(Enviroment.block_dir, block_hash.hex())
        self.assertTrue(os.path.isfile(block_file), "block content not stored in BLOCKDIR")

        # 2. A genuine Service that references the block by pointer. The packer
        #    worker builds a `pack_pb2.Service` (its `container.filesystem` is a
        #    message whose ItemBranch.file holds the inline Buffer.Block marker),
        #    so mirror that exactly.
        service = pack_pb2.Service()
        branch = service.container.filesystem.branch.add()
        branch.name = "big.bin"
        branch.file = block.SerializeToString()  # a Buffer.Block marker, inline
        _obj_id, service_dir = block_builder.build_multiblock(
            pf_object_with_block_pointers=service,
            blocks=[block_hash],
        )
        with open(os.path.join(service_dir, "_.json")) as mf:
            manifest = json.load(mf)
        self.assertTrue(
            any(isinstance(e, list) for e in manifest),
            "service dir did not become multiblock (no block pointer in _.json)",
        )
        original_hash = _sha3_of_multiblock(service_dir)

        # 3. Serialise via the REAL packer code path (un-mocked).
        metadata = celaut_pb2.Metadata()
        bee = server._serialize_bee(service_dir, metadata.SerializeToString())
        self.assertGreater(
            len(bee), 10 * 1024 * 1024,
            "the .bee is smaller than the block it should embed -> content missing, "
            "only pointers were written",
        )

        # 4. Read the .bee back into a FRESH, EMPTY block dir. This is the
        #    receiver's position: it must re-materialise the block from the
        #    stream alone.
        recv = tempfile.mkdtemp(prefix="rt-recv-")
        recv_blocks = os.path.join(recv, "blocks")
        recv_cache = os.path.join(recv, "cache")
        os.makedirs(recv_blocks)
        os.makedirs(recv_cache)
        modify_env(cache_dir=os.path.abspath(recv_cache) + os.sep,
                   block_dir=recv_blocks + os.sep)

        bee_path = os.path.join(recv, "service.celaut.bee")
        with open(bee_path, "wb") as f:
            f.write(bee)

        dirs = list(read_from_file(bee_path, indices={
            1: celaut_pb2.Metadata,
            2: celaut_pb2.Service,
        }))
        self.assertEqual(len(dirs), 2, "expected [Metadata, Service] from the bee")
        recovered_service_dir = dirs[1].dir

        # The block content must exist in the fresh receiver block dir...
        self.assertTrue(
            os.path.isfile(os.path.join(recv_blocks, block_hash.hex())),
            "block content was NOT re-materialised on read -> the .bee shipped "
            "pointers without payload",
        )
        # ...and the reconstructed service must hash identically to the original.
        self.assertEqual(
            _sha3_of_multiblock(recovered_service_dir), original_hash,
            "round-tripped service hash differs from the original",
        )


if __name__ == "__main__":
    unittest.main()
