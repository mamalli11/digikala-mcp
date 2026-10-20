---
description: Check a product's price on Digikala and Torob with two agents (collector, then a supervising advisor)
argument-hint: <product, e.g. "گوشی سامسونگ A07 64 گیگ">
---

Find out where to buy this product: $ARGUMENTS

Run this two-agent process. You only pass messages between the agents; do not collect data or decide yourself.

1. **Collect.** Call the `price-collector` agent. Give it the product text above and nothing else (no hints
   about the answer). It returns a REPORT.
2. **Audit and decide.** Call the `buy-advisor` agent. Give it the user's request and the collector's REPORT
   **verbatim and complete** (do not summarize or reword it: the advisor must see the raw evidence).
3. **Loop on doubts.** If the advisor's verdict is `NEEDS_RECHECK`, call `price-collector` again. Say it is a
   **re-check**, give the product, the ids from the first report (the Digikala id and every Torob id it used), and
   only the advisor's numbered questions, so it answers them without redoing the first round, then call `buy-advisor` again with the earlier report plus the
   new answers. At most two re-checks. If it is still `NEEDS_RECHECK`, report it as `INCONCLUSIVE`.
4. **Answer the user** in their language: the verdict, the 2-4 line reason with numbers, the risks, and the links.
   Add one line saying how many collection rounds were needed. If the two agents disagreed on anything, say so.

## Show progress

The agents run in their own context, so the user sees nothing of their work unless you say it. Write one short
line in the user's language **before** each step ("Collector: searching Digikala and Torob...", "Advisor:
auditing the report...", "Advisor asked 2 questions; collector re-checking (round 2)...") and one line **after**
it with what came back (the product chosen, the verdict, the questions). In the final answer add a "What each
agent did" list: for the collector the tools it called (copy its "Calls made" section), for the advisor each
audit point with its OK / PROBLEM / UNKNOWN mark. Never hide a disagreement or a failed tool call.

Never buy, log in or post anything: the tools are read-only.
