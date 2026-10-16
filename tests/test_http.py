import json

import httpx
import pytest
from conftest import fixture
from mcp import Client
from mcp.types import TextContent

from digikala_mcp.server import mcp

pytestmark = pytest.mark.anyio


async def test_all_tools_are_read_only(client):
    tools = (await client.list_tools()).tools
    assert len(tools) == 23
    for t in tools:
        assert t.name.startswith("dk_"), t.name
        assert t.annotations.read_only_hint is True, t.name
        assert t.description and t.title, t.name


async def test_cdn_cookie_challenge_is_followed(client, api):
    """api.digikala.com first answers 307 + digicdn_cookie to the same URL; the cookie jar passes it."""

    def challenge(request):
        if "digicdn_cookie=abc" not in request.headers.get("cookie", ""):
            return httpx.Response(
                307, headers={"Location": str(request.url), "Set-Cookie": "digicdn_cookie=abc; Path=/"}
            )
        return httpx.Response(200, json=fixture("autocomplete.json"))

    api["/v1/autocomplete/"] = challenge
    result = await client.call_tool("dk_suggest", {"query": "samsung"})
    assert not result.is_error
    assert len(api.calls) == 2
    assert api.calls[1].headers["Referer"] == "https://www.digikala.com/"


async def test_body_status_is_authoritative(client, api):
    api["/v1/autocomplete/"] = {"status": 401}
    result = await client.call_tool("dk_suggest", {"query": "samsung"})
    assert result.is_error and "status 401" in result.content[0].text


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (httpx.Response(404, json={"status": 404}), "Not found"),
        (httpx.Response(403, text="<html>Access Denied ... Error code : 403</html>"), "unknown category or brand"),
        (httpx.Response(429, json={"status": 429}), "rate limiting"),
        (httpx.Response(503, text="<html>down</html>"), "server error"),
        (httpx.Response(400, json={"status": 400, "message": "not main category"}), "not a main category"),
        (httpx.Response(200, text="<html>maintenance</html>"), "non-JSON"),
    ],
)
async def test_upstream_errors_are_actionable(client, api, response, message):
    api["/v1/best-selling/"] = lambda r: response
    result = await client.call_tool("dk_best_sellers", {"category_id": 11})
    assert result.is_error and message in result.content[0].text


async def test_network_error(client, api):
    def boom(request):
        raise httpx.ConnectError("refused", request=request)

    api["/v1/digiplus/plans/"] = boom
    result = await client.call_tool("dk_plus_plans", {})
    assert result.is_error and "Could not reach api.digikala.com" in result.content[0].text
    assert len(api.calls) == 2  # retried once


async def test_one_retry_on_5xx_but_not_on_4xx(client, api):
    hits = []

    def flaky(request):
        hits.append(1)
        return (
            httpx.Response(503, text="down") if len(hits) == 1 else httpx.Response(200, json=fixture("plus_plans.json"))
        )

    api["/v1/digiplus/plans/"] = flaky
    assert not (await client.call_tool("dk_plus_plans", {})).is_error and len(hits) == 2
    api["/v1/best-selling/"] = lambda r: httpx.Response(404, json={"status": 404})
    assert (await client.call_tool("dk_best_sellers", {})).is_error
    assert sum(r.url.path == "/v1/best-selling/" for r in api.calls) == 1


async def test_redirect_to_another_host_is_refused(client, api):
    api["/v1/autocomplete/"] = lambda r: httpx.Response(307, headers={"Location": "https://evil.example/x"})
    result = await client.call_tool("dk_suggest", {"query": "samsung"})
    assert result.is_error and "another host" in result.content[0].text
    assert all(r.url.host == "api.digikala.com" for r in api.calls)


async def test_wire_format_is_one_text_block_and_no_output_schema(api):
    """The real SDK client, without conftest's patch: one compact TextContent, no structuredContent, no outputSchema."""
    api["/v1/autocomplete/"] = fixture("autocomplete.json")
    async with Client(mcp, raise_exceptions=True) as c:
        assert all(t.output_schema is None for t in (await c.list_tools()).tools)
        result = await c.call_tool("dk_suggest", {"query": "samsung"})
    assert result.structured_content is None and len(result.content) == 1
    assert isinstance(result.content[0], TextContent) and " " not in result.content[0].text[:20]
    json.loads(result.content[0].text)


async def test_input_schemas_have_no_title_noise():
    for t in await mcp.list_tools():
        assert "title" not in t.input_schema, t.name
        assert all("title" not in p for p in t.input_schema.get("properties", {}).values()), t.name
