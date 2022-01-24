import os
import tempfile
import pytest
from dora import dora
from dotenv import load_dotenv
load_dotenv(".devenv")

@pytest.fixture
def client():
    with dora.test_client() as client:
        yield client
    #
    #    with app.app_context():
    #        init_db()
    #os.close(db_fd)
    #os.unlink(db_path)

def test_homepage(client):
    """Read the homepage"""

    response = client.get("/")
    assert response.status_code == 200

def test_gfdlvitals_plot(client):
    """ tests the gfdlvitals plots display """
    response = client.get("/analysis/scalar?region=global&realm=Atmos&smooth=&nyears=&id=%2FUsers%2Fkrasting%2Ftest")
    print(response)
