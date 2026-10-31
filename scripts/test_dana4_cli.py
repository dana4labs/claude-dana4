"""Exercise CLI argument handling through the real client, without a network."""

import contextlib
import io
import json
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import dana4_cli
import dana4_client
from dana4_client import Dana4Client
from test_dana4_client import _capture


class CliArgumentsTest(unittest.TestCase):
    def setUp(self):
        # _capture replaces the module's shared urlopen function.
        self.original_urlopen = dana4_client.urllib.request.urlopen

    def tearDown(self):
        dana4_client.urllib.request.urlopen = self.original_urlopen

    def _execute(self, *extra):
        """Run `agents-execute` with `extra` args; return (exit code, requests)."""
        client = Dana4Client(host="https://test.example", api_key="d4a_test")
        sent = _capture(client)
        with (
            patch.object(dana4_cli, "Dana4Client", return_value=client),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            code = dana4_cli.main(
                [
                    "agents-execute",
                    "--agent-username",
                    "reviewer",
                    "--tool-key",
                    "run_task",
                    "--task-id",
                    "parent-task",
                    *extra,
                ]
            )
        return code, sent

    def test_execute_accepts_plain_and_at_prefixed_input_files(self):
        original_directory = pathlib.Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            file = pathlib.Path(tmp) / "review inputs.json"
            payload = {"instructions": "Check the recommendation", "bags": 2}
            file.write_text(json.dumps(payload), encoding="utf-8")
            try:
                os.chdir(tmp)
                for name in [str(file), file.name]:
                    for prefix in ["", "@"]:
                        with self.subTest(name=name, prefix=prefix):
                            code, sent = self._execute(
                                "--inputs-file", prefix + name
                            )
                            self.assertEqual(code, 0)
                            self.assertEqual(len(sent), 1)
                            self.assertEqual(
                                json.loads(sent[0].data)["inputs"], payload
                            )
                            self.assertTrue(
                                sent[0].full_url.endswith(
                                    "/agents/reviewer/execute"
                                )
                            )
            finally:
                os.chdir(original_directory)

    def test_execute_without_inputs_still_dispatches(self):
        code, sent = self._execute()
        self.assertEqual(code, 0)
        self.assertEqual(len(sent), 1)
        self.assertNotIn("inputs", json.loads(sent[0].data))

    def test_missing_inputs_file_exits_cleanly_without_dispatch(self):
        with self.assertRaises(SystemExit) as raised:
            self._execute("--inputs-file", "@/nonexistent/inputs.json")
        self.assertIn("/nonexistent/inputs.json", str(raised.exception.code))


if __name__ == "__main__":
    unittest.main()
