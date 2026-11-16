"""Deterministic HTTPX tests using a mock transport (no external network)."""
import asyncio
import pytest
import httpx
from student_manager.external_api import fetch_with_retry, fetch_group_statistics
from student_manager.api import app

@pytest.mark.asyncio
async def test_async_transport_success():
    async def handler(request):
        return httpx.Response(200, json={'ok':True})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assert await fetch_with_retry(client, 'http://example.test/ping') == {'ok':True}

@pytest.mark.asyncio
async def test_retry_eventually_succeeds():
    calls = 0
    async def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(503 if calls < 3 else 200, json={'attempt':calls})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assert (await fetch_with_retry(client, 'http://example.test/ping', backoff=0))['attempt'] == 3
    assert calls == 3

@pytest.mark.asyncio
async def test_retry_fails_after_limit():
    async def handler(request):
        return httpx.Response(503)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_with_retry(client, 'http://example.test', attempts=2, backoff=0)

@pytest.mark.asyncio
async def test_client_error_not_retried():
    calls = 0
    async def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(404)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_with_retry(client, 'http://example.test', backoff=0)
    assert calls == 1

@pytest.mark.asyncio
async def test_request_error_retried():
    calls = 0
    async def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ConnectError('offline')
        return httpx.Response(200, json={'ok':True})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assert await fetch_with_retry(client, 'http://example.test', backoff=0) == {'ok':True}

@pytest.mark.asyncio
async def test_timeout_is_enforced():
    async def handler(request):
        await asyncio.sleep(0.05)
        return httpx.Response(200, json={'ok':True})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(TimeoutError):
            await fetch_with_retry(client, 'http://example.test', timeout=0.001, attempts=1)

@pytest.mark.asyncio
async def test_gather_limits_concurrency():
    active = 0
    maximum = 0
    async def handler(request):
        nonlocal active, maximum
        active += 1
        maximum = max(active, maximum)
        await asyncio.sleep(0.005)
        active -= 1
        return httpx.Response(200, json={'group_id':int(request.url.path.split('/')[2])})
    results = await fetch_group_statistics('http://example.test', list(range(1, 9)), concurrency=2,
                                           transport=httpx.MockTransport(handler), attempts=1)
    assert [r['group_id'] for r in results] == list(range(1, 9))
    assert maximum <= 2 and maximum == 2

@pytest.mark.asyncio
async def test_group_statistics_with_asgi_client(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from student_manager.models import Base, Group, Student
    from student_manager.dependencies import get_session
    engine = create_engine(f"sqlite:///{(tmp_path / 'async.sqlite3').as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        g1, g2 = Group(name='ФЕП-32'), Group(name='ФЕП-31')
        db.add_all([g1, g2]); db.flush()
        db.add_all([Student(first_name='Марія', last_name='Дорош', group_id=g1.id, average_grade=85),
                    Student(first_name='Олена', last_name='Романюк', group_id=g2.id, average_grade=95)])
        db.commit()
        ids = [g1.id, g2.id]
    def override():
        with Session() as db:
            yield db
    app.dependency_overrides[get_session] = override
    try:
        result = await fetch_group_statistics('http://testserver', ids, transport=httpx.ASGITransport(app=app))
        assert [row['students_count'] for row in result] == [1, 1]
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

@pytest.mark.parametrize('kwargs', [{'attempts':0},{'timeout':0},{'backoff':-0.1}])
@pytest.mark.asyncio
async def test_invalid_retry_options(kwargs):
    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError):
            await fetch_with_retry(client, 'http://example.test', **kwargs)

@pytest.mark.asyncio
async def test_invalid_semaphore():
    with pytest.raises(ValueError):
        await fetch_group_statistics('http://testserver', [1], concurrency=0)
