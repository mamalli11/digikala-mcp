import copy

import httpx
import pytest
from conftest import fixture

from digikala_mcp.torob import _profile

pytestmark = pytest.mark.anyio

DK_ID = 20109389  # recorded: Samsung Galaxy A07 64GB/4GB, cheapest offer 42,503,600 Toman
TOROB_ID = "b80e39fb-c898-4b66-ba1e-f230c9f30675"  # recorded: A07 4G (China) 64/4, 7 shops kept
NEW_A07 = ("گوشی سامسونگ A07 4G | حافظه 64 رم 4 گیگابایت", "Samsung Galaxy A07 4G 64/4 GB")  # no region word


def routes(api, search=None):
    api["/product/v1/products/20109389/"] = fixture("product.json")
    api["/v4/base-product/search/"] = search or fixture("torob_search.json")


async def test_torob_search(client, api):
    api["/v4/base-product/search/"] = fixture("torob_search.json")
    r = (await client.call_tool("torob_search", {"query": "samsung a07 64"})).structured_content
    q = api.calls[0].url.params
    assert q["q"] == "samsung a07 64" and q["size"] == "24" and q["source"] == "next_desktop"
    assert api.calls[0].headers["Origin"] == "https://torob.com"
    # priced items only: the recorded page also holds ten old listings with price 0
    assert [p["price"] for p in r["products"]] == [72099000, 40300000, 44690000, 40500000, 43000000, 51499000]
    first, a07 = r["products"][0], r["products"][1]
    assert first["ad"] is True and first["match"] == "some" and first["missing_words"] == ["a07", "64"]
    assert a07["id"] == TOROB_ID and a07["shops"] == 221 and a07["match"] == "all"
    assert a07["title_en"] == "Samsung Galaxy A07 4G (China) 64/4 GB"
    assert a07["url"] == f"https://torob.com/p/{TOROB_ID}/" and a07["image"].startswith("https://")
    assert "ad" not in a07 and "condition" not in a07 and "note" not in r


async def test_a_sponsored_and_an_organic_row_of_one_product_are_listed_once(client, api):
    """Seen live: A07 64/4 came back twice, as an ad and as a normal row."""
    body = fixture("torob_search.json")
    china = next(x for x in body["results"] if x["random_key"] == TOROB_ID)
    ad = copy.deepcopy(china)
    ad["is_adv"] = True
    body["results"].insert(0, ad)
    routes(api, body)
    r = (await client.call_tool("torob_search", {"query": "samsung a07 64"})).structured_content
    ids = [p["id"] for p in r["products"]]
    assert ids.count(TOROB_ID) == 1 and "ad" not in next(p for p in r["products"] if p["id"] == TOROB_ID)
    r = (await client.call_tool("dk_compare_with_torob", {"product_id": DK_ID})).structured_content
    ids = [c["id"] for c in r["torob"]["candidates"]]
    assert ids.count(TOROB_ID) == 1 and len(ids) == len(set(ids))


async def test_torob_search_hides_used_unless_asked(client, api):
    body = fixture("torob_search.json")
    stock = next(x for x in body["results"] if x["stock_status"])
    stock["price"] = 38000000  # the recorded used A07 has no price today
    api["/v4/base-product/search/"] = body
    r = (await client.call_tool("torob_search", {"query": "samsung a07 64"})).structured_content
    assert r["used_hidden"] == 1 and all("condition" not in p for p in r["products"])
    r = (await client.call_tool("torob_search", {"query": "samsung a07 64", "include_used": True})).structured_content
    assert "used_hidden" not in r
    assert [p["condition"] for p in r["products"] if "condition" in p] == ["کارکرده"]


async def test_torob_search_loose_results_get_a_note(client, api):
    api["/v4/base-product/search/"] = fixture("torob_search.json")
    r = (await client.call_tool("torob_search", {"query": "zzqxkjw"})).structured_content
    assert {p["match"] for p in r["products"]} == {"none"} and "loose matches" in r["note"]


async def test_torob_offers(client, api):
    api["/v4/base-product/details/"] = fixture("torob_details.json")
    r = (await client.call_tool("torob_offers", {"product_id": TOROB_ID})).structured_content
    assert api.calls[0].url.params["prk"] == TOROB_ID
    assert r["id"] == TOROB_ID and r["min_price"] == 40300000 and r["max_price"] == 72890000
    # cheapest first; the shop that lists it as out of stock is dropped
    assert r["offers_count"] == 7 and r["offers"][0]["price"] == 40300000
    assert [o["price"] for o in r["offers"]] == sorted(o["price"] for o in r["offers"])
    assert "موبوصدرا" not in [o["shop"] for o in r["offers"]]
    first = r["offers"][0]
    assert {k: first[k] for k in ("shop", "city", "price", "score", "votes", "updated")} == {
        "shop": "ایرانا مال",
        "city": "تهران",
        "price": 40300000,
        "score": 5,
        "votes": 0,  # kept: a 5 from 0 votes means nothing
        "updated": "۳۴ دقیقه پیش",
    }
    assert len(first["title"]) <= 100 and "گارانتی" in first["note"] and "ad" not in first
    assert next(o for o in r["offers"] if o["shop"] == "جی اس ام")["ad"] is True
    few = (await client.call_tool("torob_offers", {"product_id": TOROB_ID, "max_offers": 2})).structured_content
    assert len(few["offers"]) == 2
    many = await client.call_tool("torob_offers", {"product_id": TOROB_ID, "max_offers": 100})
    assert not many.is_error and len(many.structured_content["offers"]) == 7  # 100 is allowed (was 50)
    assert (await client.call_tool("torob_offers", {"product_id": TOROB_ID, "max_offers": 101})).is_error


async def test_torob_offers_errors(client, api):
    assert (await client.call_tool("torob_offers", {"product_id": "not-a-uuid"})).is_error  # rejected before any call
    assert not api.calls
    api["/v4/base-product/details/"] = lambda r: httpx.Response(404, json={"message": "Base product not found: x"})
    r = await client.call_tool("torob_offers", {"product_id": TOROB_ID})
    assert r.is_error and "Not found on api.torob.com" in r.content[0].text


async def test_torob_bot_check_reaches_the_agent(client, api):
    api["/v4/base-product/search/"] = lambda r: httpx.Response(
        490, text="<title>آیا شما یک ربات هستید؟</title>", headers={"content-type": "text/html"}
    )
    r = await client.call_tool("torob_search", {"query": "samsung a07"})
    assert r.is_error and "bot check" in r.content[0].text and "Iranian IP" in r.content[0].text


async def test_compare_flags_a_different_region_instead_of_comparing(client, api):
    """Digikala sells the plain A07; the only priced new Torob A07 64/4 is the China one: do not compare."""
    routes(api)
    r = (await client.call_tool("dk_compare_with_torob", {"product_id": DK_ID})).structured_content
    assert api.calls[1].url.params["q"].startswith("گوشی موبایل سامسونگ مدل Galaxy A07")  # the Digikala title
    assert r["digikala"]["price"] == 42503600 and r["digikala"]["in_stock"]
    assert r["digikala"]["warranty"] and r["digikala"]["url"].endswith("/dkp-20109389/")
    assert "comparison" not in r and "No new Torob product matches" in r["note"]
    china = next(c for c in r["torob"]["candidates"] if c["id"] == TOROB_ID)
    assert china["match"] == "no" and china["extra"] == ["چین"] and "missing" not in china
    other = next(c for c in r["torob"]["candidates"] if c["title_en"].endswith("(China) 128/4 GB"))
    assert other["match"] == "no" and other["missing"] == ["64"]
    assert r["torob"]["unpriced_hidden"] == 8


async def test_compare_same_product_cheaper_on_torob(client, api):
    body = fixture("torob_search.json")
    china = next(x for x in body["results"] if x["random_key"] == TOROB_ID)
    china["name1"], china["name2"] = NEW_A07
    routes(api, body)
    r = (await client.call_tool("dk_compare_with_torob", {"product_id": DK_ID})).structured_content
    assert r["comparison"] == {
        "torob_id": TOROB_ID,
        "torob_price": 40300000,
        "digikala_price": 42503600,
        "cheaper": "torob",
        "difference": 2203600,
        "difference_pct": 5.2,
    }
    assert r["torob"]["candidates"][0]["id"] == TOROB_ID and r["torob"]["candidates"][0]["match"] == "all"
    assert "note" not in r


async def test_compare_digikala_cheaper_and_used_never_best(client, api):
    body = fixture("torob_search.json")
    china = next(x for x in body["results"] if x["random_key"] == TOROB_ID)
    china["name1"], china["name2"] = NEW_A07
    china["stock_status"] = "کارکرده"  # the cheapest same-model item is used: skipped
    dearer = copy.deepcopy(china)
    dearer.update(random_key="11111111-2222-3333-4444-555555555555", price=45000000, stock_status="")
    body["results"].append(dearer)
    routes(api, body)
    r = (await client.call_tool("dk_compare_with_torob", {"product_id": DK_ID})).structured_content
    assert r["comparison"]["torob_id"] == dearer["random_key"] and r["comparison"]["cheaper"] == "digikala"
    assert r["comparison"]["difference"] == 45000000 - 42503600 and r["comparison"]["difference_pct"] == 5.9
    used = next(c for c in r["torob"]["candidates"] if c["id"] == TOROB_ID)
    assert used["match"] == "all" and used["condition"] == "کارکرده"


async def test_compare_never_trusts_a_match_at_under_half_the_price(client, api):
    """Seen live: a 'WH-1000XM5' row at 1.28M beside a 65M headphone made Torob '98% cheaper'."""
    body = fixture("torob_search.json")
    china = next(x for x in body["results"] if x["random_key"] == TOROB_ID)
    china["name1"], china["name2"] = NEW_A07
    china["price"] = 1280000
    routes(api, body)
    r = (await client.call_tool("dk_compare_with_torob", {"product_id": DK_ID})).structured_content
    assert "comparison" not in r and "under half" in r["note"]
    cheap = r["torob"]["candidates"][0]
    assert cheap["id"] == TOROB_ID and cheap["match"] == "all" and "under half" in cheap["warning"]
    legit = copy.deepcopy(china)
    legit.update(random_key="11111111-2222-3333-4444-555555555555", price=41000000)
    body["results"].append(legit)
    args = {"product_id": DK_ID, "query": "samsung a07 64"}  # another query: the 2-minute cache would replay the first
    r = (await client.call_tool("dk_compare_with_torob", args)).structured_content
    assert r["comparison"]["torob_id"] == legit["random_key"] and r["comparison"]["difference"] == 1503600
    assert r["torob"]["candidates"][0]["id"] == legit["random_key"]  # the suspicious one sorts after the sound match


async def test_compare_without_a_model_code_asks_the_agent_to_read(client, api):
    body = fixture("product.json")
    body["data"]["product"].update(title_fa="کتری برقی", title_en=None)
    api["/product/v1/products/20109389/"] = body
    api["/v4/base-product/search/"] = fixture("torob_search.json")
    args = {"product_id": DK_ID, "query": "کتری برقی", "limit": 3}
    r = (await client.call_tool("dk_compare_with_torob", args)).structured_content
    assert api.calls[1].url.params["q"] == "کتری برقی"
    assert {c["match"] for c in r["torob"]["candidates"]} == {"unknown"} and len(r["torob"]["candidates"]) == 3
    assert "comparison" not in r and "no model code" in r["note"]


def test_profile_reads_codes_and_variants_in_both_languages():
    fa = "گوشی موبایل سامسونگ مدل Galaxy S25 Ultra SM-S938B/DS دو سیم کارت ظرفیت ۲۵۶ گیگابایت و رم 12 گیگابایت - پک ویتنام"
    en = "Samsung Galaxy S25 Ultra Dual SIM 256GB And 12GB RAM Mobile Phone - Vietnam Pack"
    torob = (
        "گوشی سامسونگ (ویتنام) S25 Ultra 5G | حافظه 256 رم 12 گیگابایت Samsung Galaxy S25 Ultra 5G (Vietnam) 256/12 GB"
    )
    assert _profile(f"{fa} {en}") == ({"s25", "256", "12"}, {"ultra", "ویتنام"})  # the SM-S938B factory code is ignored
    assert _profile(torob) == ({"s25", "256", "12"}, {"ultra", "ویتنام"})
    assert _profile("iPhone 15 Pro 1TB")[0] == _profile("آیفون 15 پرو 1 ترابایت iPhone 15 Pro 1T")[0] == {"15", "1t"}
    assert _profile("Redmi Note 15 Pro 5G 256/8")[1] == {"pro"}


def test_profile_ignores_spec_numbers_but_keeps_regions():
    # '4 میکروفون' (4 microphones) is a spec Torob's short title leaves out; WH-1000XM5 is the model
    assert _profile("هدفون بی‌سیم سونی مدل WH-1000XM5 دارای 4 میکروفون") == ({"1000xm5"}, set())
    assert _profile("هدفون بی‌سیم سونی مدل WH-1000XM5")[0] == {"1000xm5"}
    assert _profile("کتری برقی کد 4480")[0] == {"4480"}  # a number after کد/مدل names the model
    assert _profile("Apple iPhone 16 CH Dual SIM 128GB") == ({"16", "128"}, {"ch"})
    assert _profile("گوشی اپل iPhone 16 حافظه ۱۲۸ رم ۸ گیگابایت")[1] == set()  # no region code: another variant
    assert _profile("آیفون 15 نان اکتیو") == _profile("آیفون 15 نات اکتیو") == (set(), {"نات", "اکتیو"})
