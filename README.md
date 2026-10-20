<!-- mcp-name: io.github.sepehr071/digikala-mcp -->

<div align="center">

<img src="https://raw.githubusercontent.com/sepehr071/digikala-mcp/main/.github/banner.png" alt="digikala-mcp: unofficial Digikala and Torob MCP server for AI agents" width="100%">

# digikala-mcp: Digikala and Torob for AI agents

**Let your AI agent shop around on Digikala (دیجی&zwnj;کالا) and check the price on Torob (ترب).**<br>
An unofficial, read-only MCP server: search Iran's largest online store, compare every seller's offer, judge a price
against 30 days of history, read reviews, and see whether Torob sells the same product cheaper. Works with Claude, Cursor and Copilot.

[![PyPI](https://img.shields.io/pypi/v/digikala-mcp?color=2563eb)](https://pypi.org/project/digikala-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/digikala-mcp)](https://pypi.org/project/digikala-mcp/)
[![CI](https://github.com/sepehr071/digikala-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sepehr071/digikala-mcp/actions/workflows/ci.yml)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-io.github.sepehr071%2Fdigikala--mcp-7c3aed)](https://registry.modelcontextprotocol.io/?q=digikala-mcp)
[![License: MIT](https://img.shields.io/badge/license-MIT-16a34a)](https://github.com/sepehr071/digikala-mcp/blob/main/LICENSE)

[![Install in Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=digikala&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJkaWdpa2FsYS1tY3AiXX0=)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_digikala--mcp-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=digikala&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22digikala-mcp%22%5D%7D)

[For AI agents](#for-ai-agents) · [Quick start](#quick-start) · [What it can do](#what-it-can-do) · [Torob price check](#torob-price-check) · [Tools](#tools) · [FAQ](#faq) · [فارسی](#فارسی)

</div>

---

## For AI agents

- **What:** unofficial MCP server for Digikala (digikala.com, Iran) and Torob (torob.com, a price comparison site). Queries in Persian or English, prices in Toman.
- **Install:** `uvx digikala-mcp` (or `claude mcp add digikala -- uvx digikala-mcp`). Transport: stdio. Needs [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.10+).
  The Torob tools are not in the PyPI release yet (0.5.0). Until the next release, run this repository: `uvx --from <path-to-clone> digikala-mcp`.
- **Auth:** none. No API key or account. Optional `DIGIKALA_MCP_PROXY` (HTTP proxy, or a comma-separated list, e.g. with an Iranian exit if Digikala or Torob blocks yours).
- **Access:** read-only. No login, cart, checkout, payment or posting, so no confirmation is needed before calling any tool.
- **Tools:** 26. 23 `dk_` tools for Digikala, 3 for Torob (`torob_search`, `torob_offers`, `dk_compare_with_torob`).
  Start with `dk_find_cheapest`, `dk_search` or `dk_best_for_budget`. Typical sequence: `dk_find_cheapest` → `dk_product` → `dk_price_history` → `dk_compare_with_torob`.
- **Use when:** finding, comparing or judging prices of products and sellers on Digikala (including the Fresh supermarket), or checking whether Torob sells the same product cheaper.
- **Do not use when:** the user wants to buy, or needs shipping cost (only calculated at checkout), or anything behind a login.
- **Output:** compact JSON. Prices in Toman, ratings 0-5 (`null` = not rated). Digikala product ids are the `<id>` of `dkp-<id>`; Torob ids are UUIDs.
- **Machine-readable:** [`server.json`](https://github.com/sepehr071/digikala-mcp/blob/main/server.json) and the
  [awesome-iran-mcp catalog](https://github.com/sepehr071/awesome-iran-mcp) (`TOOLS.md`, `servers.json`, `llms.txt`).

## Why

Digikala lists the same phone many times: different colors, memory sizes, bundles and a dozen sellers per listing,
with prices that move every day. Sorting by "cheapest" puts phone cases first. Finding *the real cheapest offer, whether
today's price is a good one, and whether another shop sells it for less* means a lot of clicking. An agent with
`digikala-mcp` does it in a few calls:

> **You:** Cheapest Samsung Galaxy A07 on Digikala, and is now a good time to buy?
>
> **Agent:** *calls* `dk_find_cheapest(query="samsung a07")` → `dk_product(product_id=20109389)` → `dk_price_history(product_id=20109389)`
>
> | Price | Model | Seller |
> |---:|---|---|
> | **42,503,600** | Galaxy A07 64 GB / 4 GB | Digikala (same-day delivery in Tehran) |
> | **44,518,000** | Galaxy A07 64 GB / 4 GB + 25 W charger | Sepahan Hamrah Yaghout |
> | **46,811,800** | Galaxy A07 128 GB / 4 GB | Digikala |
>
> The 64 GB model is cheapest at 42,503,600, sold by Digikala itself; the next seller asks 42,918,000.
> But it's not a great moment: the black one sold for 34,499,000 yesterday and 33,200,000 at its lowest this
> month. Today's best offer is about 23% above yesterday's, so waiting may pay off.

<sub>Real tool output from 2026-10-03; prices change all the time. Prices are in Toman.</sub>

## What it can do

- 🔎 **Search** the whole catalogue in Persian or English, with price, brand, feature (OS, storage, ...), color, seller and fast-delivery filters. Every result says whether its title really matches the query.
- 💸 **Find the real cheapest match**, with accessories filtered out, and every seller's offer for a product, cheapest first.
- 🏆 **Best picks for a budget**, ranked by a rating weighted by how many buyers rated it, so a 5-star item with 3 ratings doesn't beat a 4.6 with 900.
- 🏪 **Check Torob** for the same product: see whether another shop sells it for less, and list every shop with its score and warranty line. See [Torob price check](#torob-price-check).
- 📋 **Re-check a shortlist** of up to 10 products in one call: price, cheapest offer, stock, distance from the 30-day low.
- 📈 **Judge a price** with about 30 days of daily price history per color, and the lowest price that held for two days in a row.
- 🗂️ **Browse** categories, brands, sellers and best sellers, sorted by price, sales, views, newest or buyers' pick.
- ⭐ **Check quality** with reviews (stars, pros/cons, verified buyers), buyer questions with answers, and seller reputation (on-time shipping, cancellations, returns).
- ⚡ **Catch deals**: Incredible Offers and supermarket (Digikala Fresh) discounts.
- 🧾 **Extras**: side-by-side spec comparison, installment plans, Digikala Plus free-shipping plans, live gold and coin prices, and address ↔ coordinates.
- 🔒 **Read-only by design**: no login, no cart, no orders, no payment.
- 🧾 **Auditable**: set `DIGIKALA_MCP_LOG` to a file and every tool call is logged (what was asked, how long it took, whether it failed). Answers are never written.

## Quick start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/). No API key or account.

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add digikala -- uvx digikala-mcp
```
</details>

<details>
<summary><b>Claude Desktop</b></summary>

Settings → Developer → Edit Config, then add:

```json
{
  "mcpServers": {
    "digikala": { "command": "uvx", "args": ["digikala-mcp"] }
  }
}
```
</details>

<details>
<summary><b>Cursor</b></summary>

Click **Install in Cursor** above, or add the Claude Desktop block to `~/.cursor/mcp.json`.
</details>

<details>
<summary><b>VS Code (Copilot agent mode)</b></summary>

Click **Install in VS Code** above, or add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "digikala": { "type": "stdio", "command": "uvx", "args": ["digikala-mcp"] }
  }
}
```
</details>

<details>
<summary><b>Any other MCP client</b></summary>

It's a standard stdio MCP server: run `uvx digikala-mcp`, or `pip install digikala-mcp` and run `digikala-mcp`.
The Torob tools need this repository's version (see [For AI agents](#for-ai-agents)).
</details>

Then just ask:

- "Cheapest AirPods-style earbuds under 3 million Toman with at least 4 stars?"
- "Compare the Galaxy A07 64 GB and 128 GB. Is the bigger one worth the difference?"
- "Is the Galaxy A07 64 GB cheaper on Torob?"
- "Is this seller reliable? CGDG9"
- <span dir="rtl">ارزان&zwnj;ترین شیر کم&zwnj;چرب در سوپرمارکت دیجی&zwnj;کالا چند است؟</span>

## How it works

```text
  AI agent  (Claude, Cursor, Copilot, ...)
      │
      │  MCP over stdio
      ▼
  digikala-mcp  (runs on your machine)
      │
      ├──── HTTPS ───▶  api.digikala.com   products, sellers, deals, Fresh supermarket
      │
      └──── HTTPS ───▶  api.torob.com      price comparison: shops, prices, scores
```

`digikala-mcp` runs locally and calls the same public endpoints the digikala.com and torob.com web apps use. There's
no hosted server in between, no API key, and nothing about you is sent anywhere else.

## Torob price check

Torob compares prices across Iranian shops, so it's the second opinion for a Digikala product. Three tools do it:

| Tool | What it does |
|---|---|
| `dk_compare_with_torob` | Is a Digikala product cheaper on Torob? Searches Torob with the Digikala title, keeps only the same model, size and region, and returns the price difference |
| `torob_search` | Search Torob by words: the cheapest shop's price, shop count and whether each title matches the query |
| `torob_offers` | Every shop selling one Torob product, cheapest first: city, score (with votes), when the price last changed, the shop's own title and warranty line |

How `dk_compare_with_torob` decides what is the same product:

- **Same model and numbers.** It compares model codes and numbers (`a07`, `s25`, `256`, `12`), so `256GB`, `256 گیگابایت` and `256/12 GB` all mean 256.
- **Same variant and region.** `pro`, `ultra`, Apple region codes (`CH`), and Persian region words (`ویتنام`, `چین`, `استوک`, `کره`, `اکتیو`) must match. A Chinese or stock model is not the official one.
- **Used items never count.** They are listed only when you ask (`include_used`) and never used for the comparison.
- **Implausible prices never count.** A Torob row under half of Digikala's price is usually an accessory or a typo; it is flagged with `warning`.
- **Honest about doubt.** Each candidate says `match: all`, `no` (with `missing` and `extra`) or `unknown` (the title has no code or number to compare). If nothing fits, the answer says so instead of guessing.
- **Duplicates removed.** Torob often shows a product both as a sponsored row and a normal one; it is listed once.

Torob's price is the cheapest of its shops. Before you rely on it, check that shop with `torob_offers`: a score of 5 with 0
votes means nothing, and `unreliable` means Torob doubts the price.

> Torob has no public API. These tools use the endpoints torob.com itself calls, so they can break without notice.
> Torob sometimes answers with a bot check (HTTP 490). It is usually temporary: retry later, or set `DIGIKALA_MCP_PROXY`.

## Good to know

- **Search always returns something**, even for nonsense words (Digikala's search is semantic). `dk_search` marks each result `match: all / some / none` with the missing words. `dk_find_cheapest` and `dk_best_for_budget` keep only titles that contain every query word.
- **Filters by feature:** `dk_filters(category_code="mobile-phone")` lists ids like operating system → Android. Then `dk_category_products(attributes={2226: [19239]})` filters on them.
- **The 30-day low ignores one-day dips.** `dk_shortlist` compares today's price with the lowest price that held on two days in a row (`low_30d`), because Digikala's own 30-day low can be a single day of one color. `dk_price_history` gives both per color.
- **Photos:** cards carry `image`, and `dk_product` an `images` list (max 4). They are 300 px JPEGs; drop the `?x-oss-process=…` suffix for the original size.
- **Prices move several times an hour** on popular listings with many sellers. Re-check right before buying.
- **Answers are cached for 2 minutes**, so an agent repeating a call doesn't hit the site again. A timeout, 5xx or 429 is retried up to twice with backoff.
- **Groceries** come from the supermarket store. `dk_product` shows its price, which can differ from the main-store price in search results.
- **Shipping cost** is only calculated at checkout. `dk_product` shows how each offer ships, and `dk_plus_plans` the free-shipping plans.

## Tools

Digikala product ids are the number in a `digikala.com/product/dkp-<id>/` link. Every list returns compact product cards:
id, title, brand, price, discount, stock, seller, rating, a photo URL (`image`) and the product link.

<details open>
<summary><b>🔎 Find products</b> (12)</summary>

| Tool | What it does |
|---|---|
| `dk_search` | Search by words with sort, price, brand, feature, color and seller filters; flags loose title matches |
| `dk_find_cheapest` | Cheapest in-stock real matches for a query, accessories dropped, one list |
| `dk_best_for_budget` | Best-rated real matches under a budget, rating weighted by number of ratings |
| `dk_suggest` | Autocomplete: better keywords, category codes and brand ids |
| `dk_filters` | Filter options of a category or search: features (OS, storage, ...), colors, brands, sellers, price range |
| `dk_categories` | Find category codes and main-category ids |
| `dk_category_products` | Browse a category with sort and the same filters, optionally one brand |
| `dk_brand_products` | Browse a brand's products |
| `dk_seller` | A seller's rating, on-time shipping, cancellations, returns and products |
| `dk_deals` | Incredible Offers or supermarket deals, biggest discount first |
| `dk_best_sellers` | Current best sellers, overall or per main category |
| `dk_fresh_search` | Search or browse Digikala Fresh, the supermarket |
</details>

<details open>
<summary><b>📦 Products</b> (8)</summary>

| Tool | What it does |
|---|---|
| `dk_product` | Price, stock, specs and every seller's offer (color, warranty, shipping), cheapest first |
| `dk_shortlist` | Re-price up to 10 products at once: price, cheapest offer, stock, rating, distance from the 30-day low |
| `dk_price_history` | About 30 days of daily prices per color, with low and high |
| `dk_reviews` | Customer reviews with stars, pros/cons and verified-buyer flag |
| `dk_questions` | Customer questions with their top answers |
| `dk_similar` | Similar products, e.g. cheaper alternatives |
| `dk_compare` | 2-4 products side by side: the specs that differ, plus the shared ones |
| `dk_installments` | Digipay credit-line offers for a product (credit amount, monthly repayment, months) |
</details>

<details open>
<summary><b>⚖️ Torob price check</b> (3)</summary>

| Tool | What it does |
|---|---|
| `dk_compare_with_torob` | Is a Digikala product cheaper on Torob? Same model, size and region only; returns the price difference |
| `torob_search` | Search Torob by words: cheapest shop's price, shop count, match flags |
| `torob_offers` | Every Torob shop's price for one product: city, score and votes, last price change, warranty line |
</details>

<details open>
<summary><b>🧾 Other</b> (3)</summary>

| Tool | What it does |
|---|---|
| `dk_plus_plans` | Digikala Plus membership plans (free shipments) and benefits |
| `dk_gold_prices` | Live 18k gold price per gram (daily and ~3-month change) and gold coin prices |
| `dk_location` | Address → coordinates, or coordinates → address with Digikala city/province ids |
</details>

All 26 tools are annotated `readOnlyHint: true` and return compact structured JSON, so they don't flood the agent's context.

## FAQ

<details>
<summary><b>Is there a Digikala API or MCP server for AI agents?</b></summary>

Yes: `digikala-mcp` is an unofficial MCP server with 26 read-only tools for search, seller offers, price history,
reviews, deals, and a Torob price check. It calls the same public endpoints the websites use; no API key is needed.
</details>

<details>
<summary><b>How do I use it with Claude, Cursor or Copilot?</b></summary>

Add the server with `claude mcp add digikala -- uvx digikala-mcp` (or the matching config in
[Quick start](#quick-start) for Claude Desktop, Cursor and VS Code), then ask in plain language, in Persian or English.
</details>

<details>
<summary><b>Is it official, safe and free?</b></summary>

It is unofficial and not affiliated with Digikala or Torob. It is read-only (no login, cart or payment), runs on your
machine, and is free under the MIT license.
</details>

<details>
<summary><b>Digikala returns 403 or times out for me. What now?</b></summary>

Usually not: in testing the API answered from a foreign exit too. If every tool fails with "refused the request (HTTP 403)",
set `DIGIKALA_MCP_PROXY` to an HTTP proxy with an Iranian exit. (A 403 from just one call usually means an unknown
category or brand code.) System proxy variables are ignored on purpose. If Digikala serves a bot-check page, install the
optional browser fallback (`uvx --with patchright==1.63.0 digikala-mcp` or `pip install digikala-mcp[browser]`), then run
`patchright install chromium`.
</details>

<details>
<summary><b>Can it buy something for me?</b></summary>

No, and that's deliberate. It has no login and never calls the cart, checkout, payment, or review/question
posting endpoints; it only reads public data. The agent finds the best option; you tap buy on the site.
</details>

<details>
<summary><b>A product shows <code>in_stock: false</code> and no price</b></summary>

Digikala lists products that are out of stock, coming soon or discontinued. They have no current offer, so there's
no price. Searches use `in_stock_only: true` by default.
</details>

<details>
<summary><b>Why does Torob sometimes say "no match" for a product I can find on Torob?</b></summary>

Torob's short titles often leave out the RAM or the region code, and the comparison is strict on purpose: a China or
stock model is a different product from the official one. The answer lists `missing` and `extra` for the closest
candidates, so you can judge. You can also pass `query=` with other words.
</details>

<details>
<summary><b>Claude Desktop says <code>uvx</code> is not found</b></summary>

Use the full path to `uvx` (`where uvx` on Windows, `which uvx` on macOS/Linux) as `command`.
</details>

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `DIGIKALA_MCP_PROXY` | unset | HTTP proxy for every request (Digikala and Torob), e.g. `http://user:pass@host:port`. A comma-separated list is used one at a time: the next proxy takes over when one is blocked (403/429/490) or cannot connect |
| `DIGIKALA_MCP_LOG` | unset | File to append one JSON line per tool call to: time, tool, arguments, duration, ok, answer size. Answers are never written. Follow it live with `Get-Content mcp-calls.log -Wait` (PowerShell) or `tail -f` |

<a id="فارسی"></a>

## فارسی: سرور MCP دیجی&zwnj;کالا و ترب

<div dir="rtl">

**digikala-mcp** یک سرور MCP غیررسمی و فقط&zwnj;خواندنی است که به دستیار هوش مصنوعی شما (Claude، Cursor، Copilot و ...) اجازه می&zwnj;دهد:

- در **دیجی&zwnj;کالا**، بزرگ&zwnj;ترین فروشگاه اینترنتی ایران، جستجو کند و ارزان&zwnj;ترین کالای واقعی را پیدا کند؛
- قیمت **همهٔ فروشندگان** یک کالا را ببیند و تاریخچهٔ قیمت ۳۰ روزه را بررسی کند؛
- نظرات، پرسش&zwnj;وپاسخ&zwnj;ها و کارنامهٔ فروشنده را بخواند؛
- با **ترب** مقایسه کند: آیا همان کالا در فروشگاه&zwnj;های دیگر ارزان&zwnj;تر است؟

این سرور هیچ کاری در حساب شما انجام نمی&zwnj;دهد؛ فقط داده&zwnj;های عمومی را می&zwnj;خواند.

**چه کارهایی می&zwnj;کند**

- **مقایسه با ترب:** همان کالا را در ترب پیدا می&zwnj;کند، فقط نسخهٔ نو با همان مدل، حافظه و منطقه را با قیمت دیجی&zwnj;کالا مقایسه می&zwnj;کند و تفاوت را به تومان و درصد می&zwnj;گوید. کالاهای کارکرده، تکراری و قیمت&zwnj;های مشکوک (کمتر از نصف قیمت دیجی&zwnj;کالا، معمولاً لوازم جانبی یا اشتباه) کنار گذاشته می&zwnj;شوند.
- **فهرست فروشگاه&zwnj;های ترب:** همهٔ فروشگاه&zwnj;های یک کالا با قیمت، شهر، امتیاز (با تعداد رأی)، زمان آخرین تغییر قیمت و خط گارانتی.
- **جستجو** به فارسی یا انگلیسی، با فیلتر قیمت، برند، ویژگی (سیستم عامل، حافظه و ...)، رنگ، نوع فروشنده و ارسال سریع. کنار هر نتیجه می&zwnj;گوید عنوانش واقعاً با جستجو جور است یا نه.
- **ارزان&zwnj;ترین کالای واقعی:** لوازم جانبی مثل قاب و کابل کنار گذاشته می&zwnj;شوند و پیشنهاد همهٔ فروشندگان از ارزان به گران نشان داده می&zwnj;شود.
- **بهترین انتخاب با بودجه شما:** امتیاز با تعداد رأی&zwnj;ها وزن می&zwnj;گیرد، تا یک کالای ۵ ستاره با ۳ رأی از کالای ۴٫۶ ستاره با ۹۰۰ رأی جلو نزند.
- **تاریخچهٔ قیمت:** حدود ۳۰ روز قیمت روزانه برای هر رنگ، و کمترین قیمتی که دو روز پیاپی برقرار بوده (یک روز تخفیف عجیب آن را خراب نمی&zwnj;کند).
- **بررسی فهرست منتخب:** قیمت، موجودی و فاصله تا کمترین قیمت ماه برای تا ۱۰ کالا با یک درخواست.
- **کیفیت:** نظرات خریداران با نقاط قوت و ضعف و خریدار تأییدشده، پرسش&zwnj;وپاسخ&zwnj;ها، و کارنامهٔ فروشنده (ارسال به&zwnj;موقع، لغو سفارش، مرجوعی).
- **تخفیف&zwnj;ها:** شگفت&zwnj;انگیزها، پرفروش&zwnj;ها، و تخفیف&zwnj;های سوپرمارکت (دیجی&zwnj;کالا فرش).
- **بیشتر:** مقایسهٔ مشخصات فنی، طرح&zwnj;های دیجی&zwnj;کالا پلاس، قیمت لحظه&zwnj;ای طلا و سکه، و تبدیل آدرس به مختصات.
- **ثبت تماس&zwnj;ها:** با تنظیم `DIGIKALA_MCP_LOG` هر تماس ابزار (چه پرسیده شد، چقدر طول کشید، موفق بود یا نه) در یک فایل ثبت می&zwnj;شود؛ پاسخ&zwnj;ها هرگز ثبت نمی&zwnj;شوند.

**نکته&zwnj;ها**

- فقط خواندنی است: وارد حساب نمی&zwnj;شود، سبد خرید نمی&zwnj;سازد، سفارش یا نظر ثبت نمی&zwnj;کند.
- همهٔ قیمت&zwnj;ها به تومان است و امتیازها مثل سایت از ۵.
- روی سیستم خود شما اجرا می&zwnj;شود، کلید API لازم ندارد و داده&zwnj;هایتان به هیچ سرور واسطی فرستاده نمی&zwnj;شود.
- پاسخ&zwnj;ها تا ۲ دقیقه نگه داشته می&zwnj;شوند؛ قیمت ممکن است همین&zwnj;قدر از سایت عقب باشد.
- ترب API رسمی ندارد؛ اگر ترب ساختارش را عوض کند، این بخش ممکن است موقتاً کار نکند.
- هزینهٔ ارسال فقط در پایان خرید (با ورود به حساب) مشخص می&zwnj;شود و این سرور آن را نمی&zwnj;داند.

**نصب** (اول [uv](https://docs.astral.sh/uv/getting-started/installation/) را نصب کنید). در Claude Code:

</div>

```bash
claude mcp add digikala -- uvx digikala-mcp
```

<div dir="rtl">

در Claude Desktop، Cursor و بقیهٔ برنامه&zwnj;ها همان تنظیم بخش [Quick start](#quick-start) را بگذارید.
ابزارهای ترب در نسخهٔ بعدی روی PyPI می&zwnj;آیند؛ تا آن زمان از پوشهٔ همین مخزن اجرا کنید (بخش For AI agents را ببینید).

**اگر دیجی&zwnj;کالا یا ترب از ایران جواب ندادند**

اگر کاربر خارج از ایران است، هر دو سایت ممکن است درخواست&zwnj;ها را رد کنند. `DIGIKALA_MCP_PROXY` را با یک پروکسی با خروجی ایران (مثلاً `http://user:pass@host:port`) تنظیم کنید. اگر ترب صفحهٔ «آیا شما یک ربات هستید؟» داد (خطای ۴۹۰)، چند دقیقه بعد دوباره امتحان کنید.

**نمونه پرسش&zwnj;ها**

- «ارزان&zwnj;ترین گوشی سامسونگ A07 کدام است و الان قیمتش خوب است؟»
- «همین گوشی را در ترب هم پیدا کن. ارزان&zwnj;تر است یا نه؟»
- «فروشگاه&zwnj;های ترب برای گوشی A07 چه قیمتی دارند و کدام امتیاز و گارانتی معتبر دارد؟»
- «بهترین هدفون بی&zwnj;سیم تا ۳ میلیون تومان چیست؟»
- «گوشی اندرویدی با ۲۵۶ گیگ حافظه که خود دیجی&zwnj;کالا می&zwnj;فروشد، از ارزان به گران.»
- «این سه لپ&zwnj;تاپ را مقایسه کن و بگو کدام ارزش خرید دارد.»
- «امروز چه شگفت&zwnj;انگیزی برای هدفون هست؟»

**ابزارها**

| ابزار | کاربرد |
|---|---|
| `dk_search` | جستجوی کالا با فیلتر |
| `dk_find_cheapest` | ارزان&zwnj;ترین کالای واقعی |
| `dk_best_for_budget` | بهترین کالا در بودجه |
| `dk_product` | قیمت و پیشنهاد همهٔ فروشندگان یک کالا |
| `dk_price_history` | تاریخچهٔ قیمت ۳۰ روزه |
| `dk_compare_with_torob` | مقایسهٔ قیمت با ترب |
| `torob_search` | جستجو در ترب |
| `torob_offers` | فروشگاه&zwnj;های ترب برای یک کالا |
| `dk_reviews` و `dk_questions` | نظرات و پرسش&zwnj;وپاسخ |
| `dk_seller` | کارنامهٔ فروشنده |
| `dk_deals` | شگفت&zwnj;انگیزها و تخفیف&zwnj;های سوپرمارکت |
| `dk_shortlist` | بررسی دوبارهٔ تا ۱۰ کالا |
| `dk_compare` | مقایسهٔ مشخصات ۲ تا ۴ کالا |
| `dk_plus_plans` و `dk_gold_prices` | دیجی&zwnj;کالا پلاس و قیمت طلا |

کامل&zwnj;ترین فهرست در بخش [Tools](#tools) است.

**برای توسعه&zwnj;دهندگان**

- تنظیم `DIGIKALA_MCP_LOG=mcp-calls.log` را روی هر کلاینت بگذارید تا هر تماس ابزار را زنده دنبال کنید.
- تست&zwnj;ها روی پاسخ&zwnj;های ضبط&zwnj;شده اجرا می&zwnj;شوند و به شبکه نیاز ندارند (`uv run python -m pytest`).

</div>

## Development

```bash
git clone https://github.com/sepehr071/digikala-mcp && cd digikala-mcp
uv sync
uv run python -m pytest            # offline, against recorded responses
uv run python -m pytest -m live    # real API (needs an Iranian connection or a proxy)
uv run ruff check .
```

The live tests can also run on GitHub (Actions → Live → Run workflow). They are not scheduled: from GitHub's US
runners Digikala times out on a few calls each run, while the same tests pass from an Iranian connection.

Tools live in `src/digikala_mcp/catalog.py`, `product.py`, `services.py` and `torob.py`. Each is a typed async function
with a docstring that tells the agent when to use it. Issues and PRs are welcome, especially new tools and fixes for API changes.

Releases: bump the version in `pyproject.toml` and `server.json`, then push a `v*` tag. GitHub Actions tests,
publishes to PyPI and the [MCP Registry](https://registry.modelcontextprotocol.io), and creates the GitHub Release.

## Related servers

- [Technolife MCP server](https://github.com/sepehr071/technolife-mcp) for electronics prices, with installment prices
- [MasterKala MCP server](https://github.com/sepehr071/masterkala-mcp) for gadgets and phone accessories
- [awesome-iran-mcp](https://github.com/sepehr071/awesome-iran-mcp): catalog of all Iranian-service MCP servers

## Disclaimer

Unofficial and not affiliated with or endorsed by Digikala or Torob. It uses the public endpoints of the digikala.com
and torob.com web apps, which can change without notice. Please keep request rates reasonable.

## License

[MIT](https://github.com/sepehr071/digikala-mcp/blob/main/LICENSE)

If this saves you clicks, a star helps others find it.
