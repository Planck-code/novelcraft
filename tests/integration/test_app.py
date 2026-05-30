"""Integration tests for the main application flow."""
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# Use a temporary database for tests
os.environ['DATABASE_URL'] = 'sqlite:///./test_app.db'
os.environ['DATA_DIR'] = './test_data'

from app.main import app
from app.infra.db.session import init_db, engine, Base


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test and clean up after."""
    from app.infra.db.session import engine as db_engine, Base as DBBase

    DBBase.metadata.create_all(bind=db_engine)
    yield
    # Clean up test data
    DBBase.metadata.drop_all(bind=db_engine)
    db_engine.dispose()
    import shutil
    test_data_dir = Path('./test_data')
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir, ignore_errors=True)
    test_db = Path('./test_app.db')
    if test_db.exists():
        try:
            test_db.unlink()
        except PermissionError:
            pass  # Windows file lock


@pytest.fixture
def client(setup_db):
    """Create a test client with fresh DB."""
    with TestClient(app) as c:
        yield c


def test_create_import_and_analyze_flow(client):
    """End-to-end test: create novel -> import txt -> verify chapters."""
    # 1. Create novel
    response = client.post(
        '/api/v1/novels',
        json={'title': 'Test Novel', 'author_name': 'Author A'},
    )
    assert response.status_code == 200
    novel = response.json()
    assert novel['title'] == 'Test Novel'
    assert novel['total_chapters'] == 0

    # 2. Import txt with chapter headers
    txt_content = (
        'Chapter 1 Start\n'
        'The hero enters the city.\n'
        'Chapter 2 Rise\n'
        'Conflict escalates.\n'
    )
    import_response = client.post(
        f"/api/v1/novels/{novel['id']}/import-txt",
        files={'file': ('demo.txt', txt_content.encode('utf-8'), 'text/plain')},
    )
    assert import_response.status_code == 200
    task = import_response.json()
    assert task['task_type'] == 'import_txt'
    assert task['status'] == 'success'

    # 3. Verify chapters
    chapters_response = client.get(f"/api/v1/novels/{novel['id']}/chapters")
    assert chapters_response.status_code == 200
    chapters = chapters_response.json()
    assert len(chapters) >= 1


def test_list_novels(client):
    """Test listing novels."""
    response = client.get('/api/v1/novels')
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_novel_not_found(client):
    """Test getting a non-existent novel returns 404."""
    response = client.get('/api/v1/novels/99999')
    assert response.status_code == 404


def test_get_chapter_not_found(client):
    """Test getting a non-existent chapter returns 404."""
    response = client.get('/api/v1/chapters/99999')
    assert response.status_code == 404


def test_list_tasks(client):
    """Test listing tasks works."""
    response = client.get('/api/v1/tasks')
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_memory_api_endpoints(client):
    """Test memory API endpoints exist and return valid responses."""
    # Create a novel first
    resp = client.post('/api/v1/novels', json={'title': 'Memory Test'})
    assert resp.status_code == 200
    novel_id = resp.json()['id']

    # Characters endpoint
    resp = client.get(f'/api/v1/novels/{novel_id}/characters')
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # Factions endpoint
    resp = client.get(f'/api/v1/novels/{novel_id}/factions')
    assert resp.status_code == 200

    # Timeline endpoint
    resp = client.get(f'/api/v1/novels/{novel_id}/timeline')
    assert resp.status_code == 200

    # Consistency issues endpoint
    resp = client.get(f'/api/v1/novels/{novel_id}/consistency-issues')
    assert resp.status_code == 200

    # World settings endpoint
    resp = client.get(f'/api/v1/novels/{novel_id}/world-settings')
    assert resp.status_code == 200

    # Realm systems endpoint
    resp = client.get(f'/api/v1/novels/{novel_id}/realm-systems')
    assert resp.status_code == 200


def test_visualization_api_endpoints(client):
    """Test visualization API endpoints exist and return valid responses."""
    resp = client.post('/api/v1/novels', json={'title': 'Viz Test'})
    assert resp.status_code == 200
    novel_id = resp.json()['id']

    # Character graph
    resp = client.get(f'/api/v1/novels/{novel_id}/character-graph')
    assert resp.status_code == 200
    data = resp.json()
    assert 'nodes' in data
    assert 'edges' in data

    # Emotion curve
    resp = client.get(f'/api/v1/novels/{novel_id}/emotion-curve')
    assert resp.status_code == 200
    data = resp.json()
    assert 'chapters' in data

    # Character frequency
    resp = client.get(f'/api/v1/novels/{novel_id}/character-frequency')
    assert resp.status_code == 200
    data = resp.json()
    assert 'characters' in data

    # Faction evolution
    resp = client.get(f'/api/v1/novels/{novel_id}/faction-evolution')
    assert resp.status_code == 200

    # Timeline data
    resp = client.get(f'/api/v1/novels/{novel_id}/timeline-data')
    assert resp.status_code == 200

    # Stats
    resp = client.get(f'/api/v1/novels/{novel_id}/stats')
    assert resp.status_code == 200
    data = resp.json()
    assert 'total_chapters' in data
