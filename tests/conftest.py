import datasette
from datasette_test import wait_until_responds
import pytest
from subprocess import Popen, PIPE
import sys


def pytest_report_header():
    return "Datasette: {}".format(datasette.__version__)


@pytest.fixture(scope="session")
def ds_server():
    process = Popen(
        [
            sys.executable,
            "-m",
            "datasette",
            "--memory",
            "--port",
            "8129",
        ],
        stdout=PIPE,
    )
    wait_until_responds("http://localhost:8129/")
    yield "http://localhost:8129"
    process.terminate()
    process.wait()
