"""Drives mcp-lazy the way Claude Code does, against a stand-in stdio server.

    python3 -m unittest discover -s tools

Each test gets its own HOME, so the real ~/.cache/mcp-lazy is never touched.
"""

import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest

LAZY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp-lazy")
LIST_CHANGED = "notifications/tools/list_changed"

# The tool list is read from argv[1] at startup, so rewriting that file between
# sessions is a rebuild that keeps the command identical.
STAND_IN = r"""
import json, sys
tools = json.load(open(sys.argv[1]))
for line in sys.stdin:
    msg = json.loads(line)
    if "id" not in msg:
        continue
    if msg["method"] == "initialize":
        result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                  "serverInfo": {"name": "stand-in", "version": "0"}}
    elif msg["method"] == "tools/list":
        result = {"tools": tools}
    else:
        result = {"content": [{"type": "text", "text": "called"}]}
    print(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": result}), flush=True)
"""

DRAFT_V1 = [{
    "name": "createDraft",
    "description": "Creates a Gmail draft.",
    "inputSchema": {"type": "object", "properties": {"to": {"type": "string"}},
                    "required": ["to"]},
}]
DRAFT_V2 = [{
    "name": "createDraft",
    "description": "Creates a Gmail draft.",
    "inputSchema": {"type": "object", "properties": {
        "to": {"type": "string"},
        "attachments": {"type": "array", "items": {"type": "string"}}},
        "required": ["to"]},
}]


class Session:
    """One client connection to mcp-lazy; messages that are not the awaited reply pile up in notes."""

    def __init__(self, home, cmd):
        self.proc = subprocess.Popen([LAZY, "stand-in", "--"] + cmd, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True,
                                     env={**os.environ, "HOME": home})
        self.inbox = queue.Queue()
        self.notes = []
        self.last_id = 0
        self.reader = threading.Thread(target=self.pump, daemon=True)
        self.reader.start()
        self.initialized = self.request("initialize", {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "test", "version": "0"}})
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def pump(self):
        for line in self.proc.stdout:
            self.inbox.put(json.loads(line))

    def send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def request(self, method, params=None):
        self.last_id += 1
        self.send({"jsonrpc": "2.0", "id": self.last_id, "method": method, "params": params or {}})
        while True:
            msg = self.inbox.get(timeout=15)
            if msg.get("id") == self.last_id and "method" not in msg:
                return msg["result"]
            self.notes.append(msg)

    def tool_schema(self, name):
        tools = self.request("tools/list")["tools"]
        return next(t["inputSchema"] for t in tools if t["name"] == name)

    def call(self, name):
        self.request("tools/call", {"name": name, "arguments": {"to": "a@example.com"}})
        # Anything mcp-lazy sends while handling the call lands before this reply.
        self.request("ping")

    def list_changed_count(self):
        return sum(1 for m in self.notes if m.get("method") == LIST_CHANGED)

    def close(self):
        if not self.proc.stdin.closed:
            self.proc.stdin.close()
        try:
            self.proc.wait(10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self.reader.join(5)
        self.proc.stdout.close()


class CachedToolList(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = tmp.name
        server = os.path.join(self.home, "stand_in.py")
        with open(server, "w") as f:
            f.write(STAND_IN)
        self.tools_file = os.path.join(self.home, "tools.json")
        self.cmd = [sys.executable, server, self.tools_file]

    def ship(self, tools, path=None, mtime=None):
        path = path or self.tools_file
        with open(path, "w") as f:
            json.dump(tools, f)
        if mtime is not None:
            os.utime(path, (mtime, mtime))

    def open(self, cmd=None):
        session = Session(self.home, cmd or self.cmd)
        self.addCleanup(session.close)
        return session

    def first_run(self):
        session = self.open()
        session.tool_schema("createDraft")
        session.call("createDraft")
        session.close()
        return session

    def test_initialize_declares_list_changed_when_cached_server_did_not(self):
        self.ship(DRAFT_V1)
        self.first_run()
        session = self.open()
        self.assertIs(session.initialized["capabilities"]["tools"].get("listChanged"), True)

    def test_server_built_after_the_cache_lists_new_tools_from_the_start(self):
        self.ship(DRAFT_V1)
        self.first_run()
        self.ship(DRAFT_V2, mtime=time.time() + 60)
        session = self.open()
        self.assertIn("attachments", session.tool_schema("createDraft")["properties"])

    def test_rebuilt_server_tells_client_to_refetch_tools(self):
        self.ship(DRAFT_V1)
        self.first_run()
        # Back-dated: a rebuild that touched no file the command names, so only the
        # started server can reveal it.
        self.ship(DRAFT_V2, mtime=time.time() - 3600)
        session = self.open()
        self.assertNotIn("attachments", session.tool_schema("createDraft")["properties"])
        session.call("createDraft")
        self.assertEqual(session.list_changed_count(), 1)
        self.assertIn("attachments", session.tool_schema("createDraft")["properties"])

    def test_unchanged_server_never_asks_for_refetch(self):
        self.ship(DRAFT_V1)
        first = self.first_run()
        session = self.open()
        session.tool_schema("createDraft")
        session.call("createDraft")
        self.assertEqual(first.list_changed_count() + session.list_changed_count(), 0)

    def test_new_command_does_not_get_the_old_commands_tools(self):
        self.ship(DRAFT_V1)
        self.first_run()
        other_tools = os.path.join(self.home, "fork-tools.json")
        # Back-dated so only the changed command, not a newer file, can expire the cache.
        self.ship(DRAFT_V2, other_tools, mtime=time.time() - 3600)
        session = self.open([self.cmd[0], self.cmd[1], other_tools])
        self.assertIn("attachments", session.tool_schema("createDraft")["properties"])


if __name__ == "__main__":
    unittest.main()
