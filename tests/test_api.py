"""API integration tests use an isolated SQLite database per test."""
import pytest
import httpx
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from student_manager.api import app
from student_manager.dependencies import get_session
from student_manager.models import Base

@pytest.fixture
def engine(tmp_path):
    db = create_engine(f"sqlite:///{(tmp_path / 'api.sqlite3').as_posix()}")
    @event.listens_for(db, 'connect')
    def fk_on(raw, _rec):
        raw.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(db)
    yield db
    db.dispose()

@pytest.fixture
async def client(engine):
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    def session_override():
        with Session() as db:
            yield db
    app.dependency_overrides[get_session] = session_override
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://testserver') as http:
        yield http
    app.dependency_overrides.clear()

@pytest.fixture
async def data(client):
    g1 = (await client.post('/groups', json={'name':'ФЕП-32'})).json()['id']
    g2 = (await client.post('/groups', json={'name':'ФЕП-31'})).json()['id']
    s1 = (await client.post('/students', json={'first_name':'Марія','last_name':'Дорош','group_id':g1,'average_grade':86.5})).json()['id']
    s2 = (await client.post('/students', json={'first_name':'Данило','last_name':'Левицький','group_id':g2,'average_grade':95.0})).json()['id']
    s3 = (await client.post('/students', json={'first_name':'Соломія','last_name':'Климчук','group_id':g1,'average_grade':91.5})).json()['id']
    return {'g1':g1,'g2':g2,'s1':s1,'s2':s2,'s3':s3}

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get('/health')
    assert r.status_code == 200 and r.json() == {'status':'ok'}

@pytest.mark.asyncio
async def test_create_and_list_groups(client):
    r = await client.post('/groups', json={'name':'  феп-32  '})
    assert r.status_code == 201 and r.json()['name'] == 'ФЕП-32'
    assert len((await client.get('/groups')).json()) == 1

@pytest.mark.asyncio
async def test_duplicate_group_409(client):
    await client.post('/groups', json={'name':'ФЕП-32'})
    assert (await client.post('/groups', json={'name':'феп-32'})).status_code == 409

@pytest.mark.asyncio
async def test_bad_group_validation(client):
    assert (await client.post('/groups', json={'name':'  '})).status_code == 422

@pytest.mark.asyncio
async def test_student_crud(client, data):
    student = (await client.get(f"/students/{data['s1']}")).json()
    assert student['first_name'] == 'Марія'
    r = await client.patch(f"/students/{data['s1']}", json={'average_grade':99, 'group_id':data['g2']})
    assert r.status_code == 200 and r.json()['average_grade'] == 99
    assert r.json()['group_id'] == data['g2']
    assert (await client.delete(f"/students/{data['s1']}")).status_code == 204
    assert (await client.get(f"/students/{data['s1']}")).status_code == 404

@pytest.mark.asyncio
async def test_get_students_filters(client, data):
    assert len((await client.get('/students')).json()) == 3
    r = await client.get('/students', params={'group_id':data['g1'], 'min_grade':90})
    assert len(r.json()) == 1 and r.json()[0]['last_name'] == 'Климчук'
    assert len((await client.get('/students', params={'last_name':'дорош'})).json()) == 1

@pytest.mark.asyncio
async def test_group_statistics(client, data):
    r = await client.get(f"/groups/{data['g1']}/statistics")
    assert r.status_code == 200
    assert r.json()['students_count'] == 2
    assert r.json()['average_grade'] == pytest.approx(89)
    assert r.json()['best_student']['last_name'] == 'Климчук'
    assert len((await client.get(f"/groups/{data['g1']}/students")).json()) == 2

@pytest.mark.asyncio
async def test_best_student(client, data):
    assert (await client.get('/students/best')).json()['last_name'] == 'Левицький'

@pytest.mark.asyncio
async def test_empty_statistics(client):
    group = (await client.post('/groups', json={'name':'ФЕП-99'})).json()['id']
    r = (await client.get(f'/groups/{group}/statistics')).json()
    assert r['average_grade'] is None and r['students_count'] == 0 and r['best_student'] is None

@pytest.mark.asyncio
async def test_not_found(client):
    assert (await client.get('/students/9999')).status_code == 404
    assert (await client.patch('/students/9999', json={'average_grade':80})).status_code == 404
    assert (await client.delete('/students/9999')).status_code == 404
    assert (await client.get('/groups/9999/students')).status_code == 404
    assert (await client.get('/groups/9999/statistics')).status_code == 404

@pytest.mark.asyncio
async def test_invalid_grade_and_name(client, data):
    for grade in [-0.1, 100.1, 'oops', 'NaN']:
        assert (await client.post('/students', json={
            'first_name':'Олена','last_name':'Романюк','group_id':data['g1'],'average_grade':grade
        })).status_code == 422
    assert (await client.post('/students', json={
        'first_name':' ','last_name':'Романюк','group_id':data['g1'],'average_grade':50
    })).status_code == 422

@pytest.mark.asyncio
async def test_nonexistent_group_and_update(client, data):
    r = await client.post('/students', json={'first_name':'Марія','last_name':'Дорош','group_id':999,'average_grade':80})
    assert r.status_code == 404
    assert (await client.patch(f"/students/{data['s1']}", json={'group_id':999})).status_code == 404

@pytest.mark.asyncio
async def test_bad_query(client):
    assert (await client.get('/students', params={'min_grade':101})).status_code == 422
    assert (await client.get('/students', params={'group_id':0})).status_code == 422

@pytest.mark.asyncio
async def test_openapi_docs(client):
    assert (await client.get('/docs')).status_code == 200
    r = (await client.get('/openapi.json')).json()
    assert '/students/{student_id}' in r['paths']
