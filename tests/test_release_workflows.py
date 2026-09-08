"""Static contracts for release DAGs and cross-platform failure propagation."""
from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ReleaseWorkflowTests(unittest.TestCase):
    def workflows(self):
        for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
            yield path.name, yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_each_workflow_builds_bundle_once_and_consumers_use_build_identity(self):
        for name, workflow in self.workflows():
            with self.subTest(workflow=name):
                jobs = workflow["jobs"]
                self.assertIn("build", jobs)
                builders = [job_id for job_id, job in jobs.items()
                            for step in job.get("steps", []) if "python -m build" in step.get("run", "")]
                self.assertEqual(builders, ["build"])
                self.assertEqual(jobs["build"]["outputs"]["artifact-id"], "${{ steps.upload.outputs.artifact-id }}")
                self.assertEqual(jobs["build"]["outputs"]["manifest-sha256"], "${{ steps.manifest.outputs.manifest-sha256 }}")
                consumers = []
                for job_id, job in jobs.items():
                    downloads = [step for step in job.get("steps", [])
                                 if step.get("uses", "").startswith("actions/download-artifact@")]
                    if not downloads:
                        continue
                    consumers.append(job_id)
                    self.assertIn("build", job["needs"])
                    self.assertEqual(len(downloads), 1)
                    self.assertEqual(downloads[0]["with"]["artifact-ids"], "${{ needs.build.outputs.artifact-id }}")
                    self.assertEqual(downloads[0]["with"]["digest-mismatch"], "error")
                    self.assertEqual(job["env"]["MANIFEST_SHA256"], "${{ needs.build.outputs.manifest-sha256 }}")
                    runs = "\n".join(step.get("run", "") for step in job["steps"])
                    self.assertIn("--manifest-sha256", runs)
                    self.assertIn("--commit", runs)
                    self.assertNotIn("python -m build", runs)
                self.assertTrue(consumers)

    def test_publish_waits_for_both_validators_and_verifies_before_upload(self):
        workflow = dict(self.workflows())["release.yml"]
        jobs = workflow["jobs"]
        self.assertEqual(set(jobs["publish"]["needs"]), {"build", "validate-linux", "validate-windows"})
        for validator in ("validate-linux", "validate-windows"):
            self.assertTrue(any("scripts/smoke_package.py" in s.get("run", "") for s in jobs[validator]["steps"]))
        steps = jobs["publish"]["steps"]
        verify = next(i for i, s in enumerate(steps) if "release_artifacts.py verify" in s.get("run", ""))
        upload = next(i for i, s in enumerate(steps) if "gh release create" in s.get("run", ""))
        self.assertLess(verify, upload)
        self.assertIn("--verify-tag", steps[upload]["run"])

    def test_official_actions_are_sha_pinned_with_version_comments(self):
        for path in (ROOT / ".github/workflows").glob("*.yml"):
            for line in path.read_text().splitlines():
                if "uses: actions/" in line:
                    self.assertRegex(line, r"uses: actions/[a-z-]+@[0-9a-f]{40} # v[0-9]+\.[0-9]+\.[0-9]+$")

    def test_windows_multicommand_steps_check_each_native_exit(self):
        for name, workflow in self.workflows():
            for job in workflow["jobs"].values():
                for step in job.get("steps", []):
                    if step.get("shell") != "pwsh":
                        continue
                    lines = [line.strip() for line in step.get("run", "").splitlines() if line.strip()]
                    for index, line in enumerate(lines[:-1]):
                        if re.match(r"(?:python |& .*acceptance-test\.ps1)", line):
                            self.assertEqual(lines[index + 1], "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }", (name, step["name"]))


if __name__ == "__main__":
    unittest.main()
