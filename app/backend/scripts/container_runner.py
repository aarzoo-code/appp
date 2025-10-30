"""Containerized job runner helper.

This helper runs a provided command inside a Docker container (example) to better
isolate execution. It uses the `docker` CLI via subprocess. In production you should
use a proper orchestrator (Kubernetes) and stronger sandboxing.

API:
  run_in_container(command: str, timeout: int = 30, memory: str = '256m') -> (exit_code, output)

Note: This script does not execute containers in CI here — it's a scaffold to be used
when the environment has Docker available.
"""
import shlex
import subprocess
from typing import Tuple


def run_in_container(image: str, command: str, timeout: int = 30, memory: str = '256m') -> Tuple[int, str]:
    """Run `command` inside `image` using docker run. Returns (exit_code, output).

    Security notes: executing arbitrary commands in Docker still carries risk. Ensure
    the runner image is minimal and that you run containers with network disabled
    and with appropriate seccomp/apparmor profiles in production.
    """
    if not image:
        raise ValueError('image must be provided')

    # Build docker run command; disable network and remove container after exit.
    # Use --rm, --network none, limit memory and CPU as example.
    docker_cmd = (
        f"docker run --rm --network none --memory {memory} "
        f"--cpus 0.5 {image} /bin/sh -lc {shlex.quote(command)}"
    )

    try:
        proc = subprocess.run(docker_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        out = proc.stdout.decode('utf-8', errors='replace')
        return proc.returncode, out
    except subprocess.TimeoutExpired as e:
        return 124, f'Timeout after {timeout}s'
    except Exception as e:
        return 1, f'Error running container: {e}'
