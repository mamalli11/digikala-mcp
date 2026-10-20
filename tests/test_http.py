import asyncio
import json
import sys

import httpx
import pytest
from conftest import fixture
from mcp import Client
from mcp.types import TextContent

from digikala_mcp import http
from digikala_mcp.server import mcp

pytestmark = pytest.mark.anyio


async def test_all_tools_are_read_only(client):
    tools = (await client.list_tools()).tools
    assert len(tools) == 26
    for t in tools:
        assert t.name.startswith(("dk_", "torob_")), t.name
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
    assert len(api.calls) == 3  # retried twice


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


def test_is_challenge():
    html = {"content-type": "text/html"}
    assert http._is_challenge(httpx.Response(403, text="<html>Just a moment...</html>", headers=html))
    assert http._is_challenge(httpx.Response(503, text="<!doctype html><title>ArvanCloud</title>"))
    assert http._is_challenge(httpx.Response(490, text="<title>آیا شما یک ربات هستید؟ | ترب</title>", headers=html))
    assert not http._is_challenge(httpx.Response(403, text="<html>Access Denied ... Error code : 403</html>"))
    assert not http._is_challenge(httpx.Response(403, json={"status": 403}))
    assert not http._is_challenge(httpx.Response(200, text="<html></html>", headers=html))


async def test_proxy_list_rotates_on_connect_error(monkeypatch, api):
    monkeypatch.setenv("DIGIKALA_MCP_PROXY", "http://p1:1, http://p2:2")
    assert http._proxies() == ["http://p1:1", "http://p2:2"]

    def boom(request):
        raise httpx.ConnectError("down", request=request)

    api["/v1/autocomplete/"] = boom
    http._get_client()
    assert http._proxy_index == 0
    with pytest.raises(http.ApiError):
        await http._get("/v1/autocomplete/", None)
    assert http._proxy_index == 1 and http._client is None  # rebuilt with the next proxy on the next call
    monkeypatch.setenv("DIGIKALA_MCP_PROXY", "http://p1:1")
    http._get_client()
    with pytest.raises(http.ApiError):
        await http._get("/v1/autocomplete/", None)
    assert http._client is not None  # a single proxy never rotates


async def test_stale_client_does_not_rotate(monkeypatch, api):
    monkeypatch.setenv("DIGIKALA_MCP_PROXY", "http://p1:1, http://p2:2")
    old, _ = http._get_client()
    http._next_proxy(old)
    new, _ = http._get_client()
    assert http._proxy_index == 1 and new is not old
    http._next_proxy(old)  # a late failure on the retired client must not skip the proxy now in use
    assert http._proxy_index == 1 and http._client is new


async def test_challenge_cleared_by_browser_once(monkeypatch, api):
    runs = []

    async def fake_browser(proxy):
        runs.append(proxy)
        await asyncio.sleep(0.01)
        return [{"name": "clearance", "value": "ok", "domain": ".digikala.com", "path": "/"}]

    monkeypatch.setattr(http, "_browser_cookies", fake_browser)

    def guarded(request):
        if request.headers.get("cookie", "").find("clearance=ok") < 0:
            return httpx.Response(403, text="<html>Just a moment</html>", headers={"content-type": "text/html"})
        return httpx.Response(200, json={"status": 200, "data": {}})

    api["/v1/autocomplete/"] = guarded
    await asyncio.gather(http.fetch("/v1/autocomplete/", {"a": 1}), http.fetch("/v1/autocomplete/", {"a": 2}))
    assert len(runs) == 1  # the second caller reused the cookies the first one fetched

    api["/v1/best-selling/"] = lambda r: httpx.Response(403, text="<html>Just a moment</html>")
    with pytest.raises(http.ApiError) as e:  # still blocked after the one retry: final, not retried again
        await http.fetch("/v1/best-selling/")
    assert e.value.status == 403 and sum(r.url.path == "/v1/best-selling/" for r in api.calls) == 2


async def test_challenge_without_patchright(monkeypatch, api):
    monkeypatch.setitem(sys.modules, "patchright.async_api", None)  # makes the import fail
    api["/v1/autocomplete/"] = lambda r: httpx.Response(403, text="<html>Just a moment</html>")
    with pytest.raises(http.ApiError, match=r"digikala-mcp\[browser\].*patchright install chromium"):
        await http.fetch("/v1/autocomplete/")


async def test_retry_after_is_honoured_and_capped(monkeypatch, client, api):
    waits = []

    async def fake_sleep(s):
        waits.append(s)

    monkeypatch.setattr(http.asyncio, "sleep", fake_sleep)
    hits = []

    def limited(request):
        hits.append(1)
        if len(hits) == 1:
            return httpx.Response(429, json={"status": 429}, headers={"Retry-After": "3"})
        if len(hits) == 2:
            return httpx.Response(503, json={"status": 503}, headers={"Retry-After": "999"})
        return httpx.Response(200, json=fixture("plus_plans.json"))

    api["/v1/digiplus/plans/"] = limited
    assert not (await client.call_tool("dk_plus_plans", {})).is_error
    assert len(hits) == 3 and [w for w in waits if w] == [3, http.MAX_RETRY_WAIT]
    api["/v1/best-selling/"] = lambda r: httpx.Response(429, json={"status": 429})
    assert (await client.call_tool("dk_best_sellers", {})).is_error
    assert sum(r.url.path == "/v1/best-selling/" for r in api.calls) == 3  # gives up after MAX_RETRIES


async def test_each_site_gets_only_its_own_headers(api):
    api["/v1/autocomplete/"] = {"status": 200, "data": {}}
    api["/v4/base-product/search/"] = {"results": []}
    await http.fetch("/v1/autocomplete/")
    await http.fetch("/v4/base-product/search/", base=http.TOROB_API)
    dk, torob = api.calls
    assert dk.url.host == "api.digikala.com" and dk.headers["Origin"] == "https://www.digikala.com"
    assert dk.headers["x-web-client"] == "desktop"
    assert torob.url.host == "api.torob.com" and torob.headers["Origin"] == "https://torob.com"
    assert torob.headers["Referer"] == "https://torob.com/" and "x-web-client" not in torob.headers


async def test_same_path_on_two_sites_is_cached_apart(api):
    api["/v1/shared/"] = lambda r: httpx.Response(200, json={"status": 200, "host": r.url.host})
    assert (await http.fetch("/v1/shared/"))["host"] == "api.digikala.com"
    assert (await http.fetch("/v1/shared/", base=http.TOROB_API))["host"] == "api.torob.com"


async def test_torob_bot_check_is_explained_and_never_opens_the_browser(monkeypatch, api):
    async def no_browser(proxy):
        raise AssertionError("the browser rung only knows digikala.com")

    monkeypatch.setattr(http, "_browser_cookies", no_browser)
    html = {"content-type": "text/html"}
    api["/v4/base-product/search/"] = lambda r: httpx.Response(
        490, text="<title>آیا شما یک ربات هستید؟</title>", headers=html
    )
    with pytest.raises(http.ApiError, match="bot check") as e:
        await http.fetch("/v4/base-product/search/", base=http.TOROB_API)
    assert e.value.status == 490 and "api.torob.com" in str(e.value)
    assert len(api.calls) == 2  # one retry after the first block, then final


async def test_redirect_off_torob_is_refused(api):
    api["/v4/base-product/search/"] = lambda r: httpx.Response(307, headers={"Location": "https://api.digikala.com/x"})
    with pytest.raises(http.ApiError, match="another host"):
        await http.fetch("/v4/base-product/search/", base=http.TOROB_API)


async def test_tool_calls_are_logged_only_when_asked(client, api, monkeypatch, tmp_path):
    api["/v1/autocomplete/"] = fixture("autocomplete.json")
    await client.call_tool("dk_suggest", {"query": "samsung"})  # no DIGIKALA_MCP_LOG: nothing is written
    log = tmp_path / "calls.log"
    monkeypatch.setenv("DIGIKALA_MCP_LOG", str(log))
    await client.call_tool("dk_suggest", {"query": "سامسونگ"})
    api["/v1/best-selling/"] = lambda r: httpx.Response(404, json={"status": 404})
    assert (await client.call_tool("dk_best_sellers", {})).is_error
    first, second = (json.loads(line) for line in log.read_text(encoding="utf-8").splitlines())
    assert first["tool"] == "dk_suggest" and first["args"] == {"query": "سامسونگ"} and first["ok"] is True
    assert first["chars"] > 0 and first["ms"] >= 0 and len(first["time"]) == 8
    assert second["tool"] == "dk_best_sellers" and second["ok"] is False and "Not found" in second["error"]
    assert "keywords" not in log.read_text(encoding="utf-8")  # sizes and arguments only, never the answer


async def test_a_bad_log_path_never_breaks_a_tool(client, api, monkeypatch, tmp_path):
    api["/v1/autocomplete/"] = fixture("autocomplete.json")
    monkeypatch.setenv("DIGIKALA_MCP_LOG", str(tmp_path / "no" / "such" / "dir" / "calls.log"))
    assert not (await client.call_tool("dk_suggest", {"query": "samsung"})).is_error
