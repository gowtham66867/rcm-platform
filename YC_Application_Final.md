# YC Application — TexMed
### The operating system for behavioral health billing teams

---

## Company

**Company name:** TexMed

**One-liner:**
TexMed replaces the WhatsApp group that behavioral health billing teams
use as their operating system — catching hidden payer clawbacks, tracking
SCA and ERA enrollments, and gating claims on compliance before
submission.

---

## What are you building?

Behavioral health providers (addiction treatment centers, mental health
clinics, detox facilities) lose 15-20% of collectible revenue to
operational failures that happen between their EHR and their billing team.
These aren't coding errors or denial appeals — they're the invisible
failures: a payer clawing back a $17,875 payment against a 5-year-old
debt buried in an EOB footer; an ERA enrollment missed for 18 of 25
payers, leaving the team manually posting remittances; a bank account
switch deadline that, if missed, routes all incoming payments to an
account that no longer exists.

Every one of these failures is currently caught — or missed — over a
WhatsApp group between the billing team and the provider's office manager.

TexMed is the platform that replaces that WhatsApp group. It monitors
every incoming EOB for hidden recoupment and offset language, tracks
Single Case Agreement approvals and visit counts per patient and payer,
manages ERA and EFT enrollment status across all active payers, and gates
claim submission on confirmed consent documentation — all in one
dashboard built specifically for behavioral health billing workflows.

---

## Why did you pick this idea?

I run TexMed, a revenue cycle management company that manages billing for
behavioral health providers. I didn't pick this idea — I lived it.

On June 11, 2026, our billing team discovered that Anthem had paid a
$17,875.09 claim for a patient ("Faten Haddad") but buried a line at the
bottom of the EOB reading "OUTSTANDING NEGBAL WITH DIFFER: $18,020.11" —
clawing back the entire payment against an unrelated balance from a 2021
claim. Our biller caught it by reading every line of the remittance
manually. No software flagged it. Had she missed it, we would have booked
$17,875 in revenue that we never actually received.

That same week: a billing specialist set up ERA enrollments for a new
provider, pulling from the wrong list and missing all TPAs — leaving 75%
of claims requiring manual posting and creating an AR aging crisis. A
bank account switch deadline meant that if 25+ payer EFT enrollments
weren't updated by Friday, all incoming payments would route to a closed
account. A Cigna prior-auth approval for a patient cohort was sitting
unused because no one had confirmed the consent paperwork was signed —
leaving a new clinic unable to bill a single claim for six weeks.

All of this coordination was happening over a WhatsApp group named
"Tidemark Escalations Group." Not a ticketing system. Not a platform.
A WhatsApp group with 15 members.

We built TexMed because we are the customer. Our own operations are the
product spec.

---

## How far along are you?

**Built and working:**
- EOB recoupment/offset detector — parses PDF and 835 EDI remittances,
  flags hidden clawback language with payer-specific pattern recognition
  (Anthem, Aetna, UHC, Cigna, Medicaid), cross-references against a
  claims ledger to catch payer phrasing we haven't seen before, computes
  net cash actually received vs. what the EOB appears to show.
  Correctly identified the Anthem/Haddad $18,020 clawback case against
  a $17,875 payment in our own live operations.
- Batch processing across multiple EOBs — shows aggregate hidden
  recoupment dollars across a full remittance batch.
- Live demo app at localhost — billing team can upload EOBs directly
  and see flagged results without touching code.

**In progress:**
- SCA lifecycle tracker (Single Case Agreements: patient, payer,
  provider, approved date range, approved visit count, contracting
  verification with State Medicaid)
- ERA/EFT enrollment status board (per-facility payer enrollment
  tracker with deadline alerts)
- Pre-billing consent gate (flags patients missing required consent
  documentation before claims are submitted)

**Distribution:**
- 121 warm leads in our outreach pipeline — behavioral health providers
  we've already contacted through TexMed's existing RCM business.
- Tidemark Therapy is our first pilot client — the billing team whose
  WhatsApp transcripts are our product spec.

---

## What is your business model?

SaaS subscription per provider facility, priced by monthly claim volume:

- **Starter** ($299/month): up to $500K/month in claims — solo practices,
  small outpatient groups
- **Growth** ($599/month): up to $2M/month in claims — mid-size
  residential and PHP/IOP programs
- **Enterprise** ($1,200+/month): unlimited claims, multi-location,
  custom payer pattern library

Optional success-fee layer: 5% of dollars recovered or protected in the
first 90 days, capped at the first year's subscription cost — lets us
land clients on ROI rather than a budget conversation.

**Payback period:** the Anthem/Haddad case alone ($18,020 protected)
covers 5 years of our Growth tier subscription in a single flagged claim.

---

## Who are your competitors, and what do you understand that they don't?

**What's funded in this space:**
- Sohar Health, Health Harbor — eligibility/benefits verification
  (front-end, one-time check, not ongoing monitoring)
- Klarify, Beacon Health (W26) — prior authorization automation
- Harbera (W25), Arctic Health — provider credentialing
- Aegis, Avelis Health — denial appeals and post-payment claim auditing

**What none of them do:**
None of these tools are built for behavioral health specifically. None
catch recoupments and offsets in EOBs. None manage SCA lifecycle (a
behavioral-health-specific authorization type). None track ERA/EFT
enrollment status across payer portfolios. None replace the operational
coordination layer — the WhatsApp group.

**What we understand that they don't:**
Behavioral health billing fails differently from general healthcare
billing. The failure modes are operational, not clinical: missed SCA
visit counts, incorrect ERA enrollment, EFT bank switch deadlines, consent
documentation gaps, claim routing to the wrong clearinghouse. These are
coordination and compliance failures that happen between the EHR and the
billing team — a layer none of the funded RCM tools are built to address.
The proof is five months of WhatsApp transcripts from our own billing
operations.

---

## How big could this be?

**Immediate TAM — behavioral health:**
- ~25,000-30,000 behavioral health provider organizations in the US
  (17,500 substance use treatment facilities + ~15,400 mental health
  facilities, SAMHSA/KFF 2024 data)
- At $599/month average contract: $179M SaaS TAM in behavioral health
  alone
- At 1-3% of collected revenue lost to operational failures per facility
  (conservative, based on our own operations): $1B+ in annual recoverable
  leakage this platform sits on top of

**Expansion TAM — all outpatient specialty healthcare:**
The same operational failure modes (ERA enrollment gaps, EFT switches,
consent documentation, SCA-equivalent single-case authorizations) exist
in every specialty practice that uses multiple EHRs, multiple
clearinghouses, and outsources billing to a third-party team. That's
physical therapy, behavioral health, chiropractic, addiction medicine —
a $50B+ services market with the same coordination problem.

---

## Why you?

I operate TexMed. Our team manages billing for real behavioral health
providers today. The WhatsApp transcripts that form our product spec are
from our own live client operations — not user interviews, not desk
research.

We didn't identify a market gap and then build a product. We built
a product because our own operations demanded it, and we realized the
tool we needed didn't exist. That's the only version of founder-market
fit that compounds: we are the customer, we are the distribution channel,
and every new client we onboard to TexMed's RCM services is a pilot user
for the platform before they're a paying SaaS customer.

The first 10 customers are already in our pipeline. The first pilot is
already running. The first real dollar amount we protected — $18,020 — is
already documented.

---

## What would you do with YC funding?

1. **Hire one engineer** to accelerate the SCA tracker, ERA/EFT enrollment
   board, and consent gate from prototype to production-ready.
2. **Convert 10 pipeline leads to paying customers** in the first 90 days,
   using the Anthem/Haddad case as the anchor sales story.
3. **Build the payer-pattern library** — instrument every real EOB
   processed to accumulate payer-specific recoupment phrasing across
   Anthem, Aetna, UHC, Cigna, and Medicaid MCOs. This is the data moat
   that makes the platform defensible.
4. **Apply for HIPAA BAA coverage** and move from local demo to a
   hosted, HIPAA-compliant product that can onboard clients without
   manual setup.

---

*TexMed — gowtham@texmed.us — texmed.us*

---

**Note before submitting:**
Replace synthetic demo metrics with real numbers once:
- [ ] Detector has run against 10+ real (redacted) TexMed EOBs
- [ ] At least one real outside facility has confirmed interest/signed LOI
- [ ] Tidemark pilot has a documented dollar figure (claims caught, hours
      saved) after 2-4 weeks of real usage
