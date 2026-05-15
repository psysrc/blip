import pytest
import subprocess


blip_binary = "./build/bin/blip"


def run_blip(blip_args: list[str], stdin: str) -> subprocess.CompletedProcess:
    prog_args = [blip_binary, "-"] + blip_args
    return subprocess.run(prog_args, input=stdin, text=True, capture_output=True)


@pytest.fixture(scope="session", autouse=True)
def build_blip_binary():
    """Run the build script to get the blip executable."""

    subprocess.run(["./build.sh"], check=True)  # Build the blip CLI tool

    result = subprocess.run([blip_binary, "--help"], stdout=subprocess.DEVNULL)  # Check it built correctly
    if result.returncode != 0:
        raise RuntimeError(f"Failed to build blip executable: {result.stderr}")
