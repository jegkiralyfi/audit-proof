"""Compatibility shim for the repo2docker readiness runner.

The actual execution-readiness stub now lives in `packages.checks.runners.repo2docker`.
A future build can replace this shim with a true repo2docker execution wrapper.
"""

from packages.checks.runners.repo2docker import Repo2DockerCheckRunner

__all__ = ["Repo2DockerCheckRunner"]
