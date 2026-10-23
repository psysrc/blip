import subprocess

import pytest
from filelock import FileLock

blip_binary = "./build/bin/blip"


def run_blip(blip_args: list[str], stdin: str) -> subprocess.CompletedProcess:
    """
    Run the Blip CLI tool with the provided arguments and stdin stream.

    Returns the results of the program execution (`subprocess.CompletedProcess`).
    """

    prog_args = [blip_binary, "-", *blip_args]
    return subprocess.run(prog_args, input=stdin, text=True, capture_output=True, check=False)


def run_blip_on_file(blip_args: list[str], blip_file: str) -> subprocess.CompletedProcess:
    """
    Run the Blip CLI tool with the provided arguments and a file on disk.

    Returns the results of the program execution (`subprocess.CompletedProcess`).
    """

    prog_args = [blip_binary, blip_file, *blip_args]
    return subprocess.run(prog_args, text=True, capture_output=True, check=False)


def build() -> None:
    """Run the build script and check the blip executable was successfully created."""

    subprocess.run(["./build.sh"], check=True)

    result = subprocess.run([blip_binary, "--help"], stdout=subprocess.DEVNULL, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to build blip executable: {result.stderr}")


@pytest.fixture(scope="session", autouse=True)
def build_blip_binary(tmp_path_factory: pytest.TempPathFactory, worker_id: str):
    """Build the blip executable once, however many xdist workers share the run."""

    if worker_id == "master":  # Not running under xdist
        build()
        return

    shared = tmp_path_factory.getbasetemp().parent  # Common to every worker in this run
    with FileLock(shared / "blip_build.lock"):
        done = shared / "blip_build.done"
        if not done.exists():
            build()
            done.touch()
