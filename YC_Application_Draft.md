# YC Application Draft — Recoupment/Offset Detector (TexMed)

## What are you working on?

We're building a tool that catches hidden payer recoupments in healthcare
EOBs before they get silently booked as lost revenue. When an insurance
payer pays a claim but claws the money back against an old, unrelated
balance, that clawback is often buried in fine print on the remittance —
not flagged anywhere a biller would normally look. Our tool parses every
incoming EOB, flags these hidden offsets automatically, and tells the
billing team the real cash they received versus what the EOB appears to
show.

We're starting with behavioral health providers (addiction treatment,
mental health), where billing teams are small, payer rules are unusually
messy, and this leakage is currently caught by hand — if at all.

## Why now?

Claim denial rates have climbed from 10.2% to 11.8% in the last few years,
and average denied-claim dollar amounts are rising 12-14% year over year.
Payers are getting more aggressive about recoupments and offsets, while
the billing teams catching them are still small, manual, and under-tooled
— especially at behavioral health providers, which don't have the
dedicated RCM/audit departments that large hospital systems do. The gap
between payer sophistication and provider-side tooling is widening, not
closing.

## How did you come up with this idea?

I run TexMed, a revenue-cycle management company for behavioral health
providers. Our billing team found this problem live, in our own
operations: a claim for a patient ("Faten Haddad") showed a $17,875.09
payment from Anthem, but buried at the bottom of the EOB was a line
reading "OUTSTANDING NEGBAL WITH DIFFER: $18,020.11" — Anthem was
clawing back the entire payment against an unrelated balance from a
claim dated 2021. Our biller only caught it by manually reading every
line of the EOB. That's the moment we realized: this isn't a one-off,
it's a structural blind spot industry-wide, and nobody is building
software to catch it automatically.

## What's your traction so far?

- Built and tested a working prototype against our own real EOB data;
  it correctly identified the Anthem recoupment and computed the true
  net cash received (-$145.02, not the $17,875.09 the EOB appears to
  show).
- TexMed already has a pipeline of 121 behavioral health provider leads
  from outreach we've run for our existing RCM business — our first
  customers for this product are leads we already have a relationship
  with.
- We are the customer: TexMed's own billing operation is actively
  losing money to exactly this problem, so we have a live, internal
  testbed before we sell externally.

## Why are you the right team to build this?

I've operated TexMed's RCM business for behavioral health providers and
have lived this exact failure mode inside my own company. I have direct
access to real EOBs, real billing staff, and real payer relationships —
not a hypothesis about the market, but a documented loss we caught
ourselves. That gives us a working data set, a internal pilot customer,
and a warm distribution channel on day one, instead of starting from
zero.

## What is your business model?

SaaS subscription per provider, priced by claim volume (roughly
$300-$800/month for a small-to-mid-size behavioral health facility),
with an optional success-fee layer (5-10% of dollars flagged/recovered)
once a facility has volume worth it. Payback on a single caught
recoupment like the Haddad case covers a year of subscription.

## How big could this be?

There are roughly 25,000-30,000 behavioral health treatment facilities
in the US. At a conservative estimate of 1-3% of collected revenue lost
to hidden recoupments per facility, that's $1B+ in annual leakage across
this vertical alone — before expanding into the broader healthcare RCM
market, where the same blind spot exists at every payer-provider
relationship in the country.

---
*Draft — refine traction numbers once real pilot data (vs. synthetic
test case) is available, and tighten TAM math with sourced citations
before submitting.*
