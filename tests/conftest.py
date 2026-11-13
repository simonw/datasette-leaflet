import datasette
from datasette_test import wait_until_responds
import json
import pytest
import sqlite3
from subprocess import Popen, PIPE
import sys


def pytest_report_header():
    return "Datasette: {}".format(datasette.__version__)


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    # Datasette sends "Referrer-Policy: no-referrer" for table pages, so the
    # tests that need that header load /data/places
    path = str(tmp_path_factory.mktemp("db") / "data.db")
    db = sqlite3.connect(path)
    with db:
        db.execute("create table places (id integer primary key, name text)")
        db.execute("insert into places (name) values ('Null Island')")
    db.close()
    return path


def _serve(db_path, port, *extra_args):
    process = Popen(
        [sys.executable, "-m", "datasette", db_path, "--port", str(port)]
        + list(extra_args),
        stdout=PIPE,
    )
    url = "http://localhost:{}".format(port)
    try:
        wait_until_responds(url + "/")
        yield url
    finally:
        process.terminate()
        process.wait()


@pytest.fixture(scope="session")
def ds_server(db_path):
    yield from _serve(db_path, 8129)


@pytest.fixture(scope="session")
def ds_server_no_tile_referrer_policy(db_path, tmp_path_factory):
    # Datasette with the tile_referrer_policy plugin setting turned off
    metadata = tmp_path_factory.mktemp("metadata") / "metadata.json"
    metadata.write_text(
        json.dumps({"plugins": {"datasette-leaflet": {"tile_referrer_policy": False}}})
    )
    yield from _serve(db_path, 8130, "--metadata", str(metadata))
