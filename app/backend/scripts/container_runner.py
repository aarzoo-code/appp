"""Minimal container runner helper.

This is a lightweight helper used by the worker scaffold to execute a command inside
a Docker container. It is intentionally simple and synchronous. In production you
should replace this with a robust sandbox (gVisor, Firecracker, K8s pods with resource limits).

API:
  run_in_container(image: str, cmd: str, timeout: int, memory: str) -> (exit_code:int, output:str)

The function returns the process exit code and combined stdout/stderr output.
"""
import subprocess
import shlex
import tempfile
import os
from typing import Tuple


def run_in_container(image: str, cmd: str, timeout: int = 30, memory: str = '256m') -> Tuple[int, str]:
    """Run `cmd` inside a transient Docker container created from `image`.

    Notes:
    - Uses `docker run --rm --network none` to limit network access by default.
    - Mounts a temporary directory for working files.
    - This helper is for development and testing only.
    """
    workdir = tempfile.mkdtemp(prefix='appp-runner-')
    try:
        # build the docker run command
        # Use sh -c to allow complex commands
        docker_cmd = (
            f"docker run --rm --network none -m {shlex.quote(memory)} "
            f"-v {shlex.quote(workdir)}:/work -w /work {shlex.quote(image)} sh -c {shlex.quote(cmd)}"
        )
        proc = subprocess.run(docker_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        out = proc.stdout.decode('utf-8', errors='replace')
        return proc.returncode, out
    except subprocess.TimeoutExpired:
        return 124, 'timeout'
    except Exception as e:
        return 1, f'error launching container: {e}'
    finally:
        try:
            # cleanup working dir
            for root, dirs, files in os.walk(workdir, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except Exception:
                        pass
            os.rmdir(workdir)
        except Exception:
            pass
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


def run_detached(image: str, command: str, memory: str = '256m') -> str:
    """Start container detached and return container id string."""
    docker_cmd = (
        f"docker run -d --network none --memory {shlex.quote(memory)} --cpus 0.5 "
        f"-v /tmp:/work {image} /bin/sh -lc {shlex.quote(command)}"
    )
    try:
        out = subprocess.check_output(docker_cmd, shell=True)
        cid = out.decode('utf-8').strip()
        return cid
    except Exception as e:
        raise RuntimeError(f'Failed to start container: {e}')


def is_running(container_id: str) -> bool:
    try:
        out = subprocess.check_output(f"docker inspect -f '{{{{.State.Running}}}}' {shlex.quote(container_id)}", shell=True)
        return out.decode('utf-8').strip().lower() == 'true'
    except Exception:
        return False


def kill_container(container_id: str) -> None:
    try:
        subprocess.run(f"docker kill {shlex.quote(container_id)}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def get_exit_code(container_id: str) -> int:
    try:
        out = subprocess.check_output(f"docker inspect -f '{{{{.State.ExitCode}}}}' {shlex.quote(container_id)}", shell=True)
        return int(out.decode('utf-8').strip())
    except Exception:
        return -1


def get_logs(container_id: str) -> str:
    try:
        out = subprocess.check_output(f"docker logs {shlex.quote(container_id)}", shell=True)
        return out.decode('utf-8', errors='replace')
    except Exception:
        return ''
