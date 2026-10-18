import asyncio

import httpx

from backend.main import app


def test_health_endpoint_reports_api_liveness() -> None:
    async def request() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            return await client.get("/health")

    response = asyncio.run(request())
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "arteria-backend"}


def test_analysis_endpoints_require_valid_requests() -> None:
    async def requests() -> list[httpx.Response]:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            return [
                await client.post(path, json={})
                for path in ("/analyze", "/propose", "/evaluate")
            ]

    responses = asyncio.run(requests())
    assert [response.status_code for response in responses] == [422, 422, 422]


def test_configured_local_origin_receives_cors_header() -> None:
    async def request() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            return await client.get("/health", headers={"Origin": "http://localhost:5173"})

    response = asyncio.run(request())
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
