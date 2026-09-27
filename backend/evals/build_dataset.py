"""
Generates a reproducible lease corpus and a large golden QA dataset.

Every lease is assembled from a template with randomized-but-recorded facts, so
each question has an exact ground-truth answer, an exact gold page number, and
an exact gold clause. That makes retrieval and citation accuracy checkable
without an LLM in the loop.

Run:  python -m evals.build_dataset
Out:  tests/evaluation/data/corpus.json
      tests/evaluation/data/golden_qa_large.json
"""

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "tests" / "evaluation" / "data"

SEED = 20260906
NUM_LEASES = 6

FIRST_NAMES = ["Amara", "Devin", "Priya", "Marcus", "Elena", "Tobias", "Nadia", "Colin"]
LAST_NAMES = ["Okafor", "Reyes", "Lindqvist", "Baptiste", "Moreau", "Hollis", "Ferrara", "Whitlock"]
STREETS = ["Alder Court", "Bellweather Lane", "Cormorant Way", "Dunmore Street",
           "Everly Terrace", "Fairholm Avenue", "Grangemouth Road", "Halloway Drive"]
CITIES = [("Portland", "Oregon"), ("Austin", "Texas"), ("Denver", "Colorado"),
          ("Raleigh", "North Carolina"), ("Boise", "Idaho"), ("Tacoma", "Washington")]


def money(n: int) -> str:
    return f"${n:,}.00"


def make_facts(rng: random.Random, idx: int) -> dict:
    """Pick the randomized facts for one lease. These become the ground truth."""
    rent = rng.choice([1450, 1675, 1850, 2100, 2375, 2600, 2950, 3250])
    city, state = CITIES[idx % len(CITIES)]
    deposit_multiplier = rng.choice([1.0, 1.5, 2.0])

    return {
        "lease_index": idx,
        "tenant": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
        "landlord": f"{rng.choice(LAST_NAMES)} Property Holdings, LLC",
        "unit": f"{rng.randint(100, 899)} {rng.choice(STREETS)}, Unit {rng.randint(1, 40)}",
        "city": city,
        "state": state,
        "rent": rent,
        "deposit": int(rent * deposit_multiplier),
        "deposit_multiplier": deposit_multiplier,
        "deposit_return_days": rng.choice([14, 21, 30, 45]),
        "commence": rng.choice(["January 1, 2027", "March 1, 2027", "June 1, 2027", "October 1, 2026"]),
        "expire": rng.choice(["December 31, 2027", "February 28, 2028", "May 31, 2028", "September 30, 2027"]),
        "term_months": rng.choice([12, 18, 24]),
        "grace_day": rng.choice([3, 5, 7]),
        "late_fee": rng.choice([35, 50, 75, 100]),
        "nsf_fee": rng.choice([25, 40, 60]),
        "daily_late_fee": rng.choice([5, 10, 15]),
        "guest_days": rng.choice([7, 10, 14, 21]),
        "max_occupants": rng.choice([2, 3, 4]),
        "pet_deposit": rng.choice([200, 300, 450, 500]),
        "pet_rent": rng.choice([25, 35, 50, 75]),
        "pet_weight": rng.choice([25, 35, 50, 80]),
        "entry_notice_hours": rng.choice([24, 48]),
        "termination_notice_days": rng.choice([30, 60]),
        "early_termination_months": rng.choice([1, 2, 3]),
        "holdover_multiplier": rng.choice([125, 150, 200]),
        "cure_days": rng.choice([3, 5, 10, 14]),
        "insurance_coverage": rng.choice([100000, 200000, 300000, 500000]),
        "parking_spaces": rng.choice([1, 2]),
        "parking_fee": rng.choice([0, 45, 75, 120]),
        "quiet_start": rng.choice(["9:00 PM", "10:00 PM", "11:00 PM"]),
        "key_replacement_fee": rng.choice([25, 50, 85]),
        "smoke_detector_days": rng.choice([3, 5, 7]),
    }


BOILERPLATE = [
    "Tenant acknowledges having read and understood each provision of this Agreement and has been "
    "afforded the opportunity to seek independent legal counsel prior to execution.",
    "No waiver by Landlord of any breach of any provision hereof shall be construed as a waiver of "
    "any continuing or succeeding breach of such provision or a waiver of the provision itself.",
    "If any provision of this Agreement is held to be invalid or unenforceable by a court of "
    "competent jurisdiction, the remaining provisions shall continue in full force and effect.",
    "All notices required under this Agreement shall be in writing and delivered personally, by "
    "certified mail with return receipt requested, or by electronic mail to the addresses on file.",
    "Time is of the essence with respect to the performance of every provision of this Agreement in "
    "which time of performance is a factor.",
    "The headings used in this Agreement are for convenience of reference only and shall not be used "
    "in construing or interpreting the scope or intent of any provision.",
    "Tenant shall comply with all applicable federal, state, and municipal statutes, ordinances, and "
    "regulations governing the occupancy and use of residential premises.",
    "This Agreement shall be binding upon and inure to the benefit of the heirs, executors, "
    "administrators, successors, and permitted assigns of the respective parties.",
    "Landlord reserves the right to adopt reasonable written rules and regulations governing the "
    "common areas, provided such rules are applied uniformly to all residents.",
    "Tenant shall not permit any activity on the Premises that increases the rate of insurance or "
    "that constitutes a nuisance to neighboring residents.",
    "Any personal property remaining on the Premises after Tenant vacates shall be handled in "
    "accordance with applicable state abandoned-property procedures.",
    "The parties agree that electronic signatures affixed to this Agreement shall carry the same "
    "legal force and effect as original handwritten signatures.",
    "Tenant shall maintain the heating system at a minimum of 55 degrees Fahrenheit during winter "
    "months to prevent freezing of pipes and resulting water damage.",
    "Landlord shall not be responsible for loss or damage to Tenant's personal property arising from "
    "theft, vandalism, fire, water intrusion, or any other cause not attributable to Landlord.",
    "Tenant agrees to permit Landlord to place customary 'For Rent' signage on the Premises during "
    "the final sixty days of the term.",
    "Smoking of any substance is prohibited inside the dwelling unit, in common interior areas, and "
    "within twenty-five feet of any building entrance or operable window.",
    "Tenant shall promptly notify Landlord in writing of any change to Tenant's employment, contact "
    "telephone number, or emergency contact information.",
    "Landlord may apply payments received to any outstanding balance in the order Landlord elects, "
    "regardless of any notation appearing on Tenant's payment instrument.",
]


def pad(rng: random.Random, lines: list[str], count: int) -> list[str]:
    """Append realistic boilerplate so each page is a full page of text, not a stub."""
    picks = rng.sample(BOILERPLATE, min(count, len(BOILERPLATE)))
    return lines + [""] + picks


def build_pages(f: dict) -> list[dict]:
    """Render one lease as a list of pages. Page numbers here are the gold labels."""
    r = f["rent"]
    # deterministic per-lease padding, seeded off the lease index
    prng = random.Random(SEED + f["lease_index"])
    pages: list[list[str]] = []

    # ---- Page 1: parties, property, term -----------------------------------
    pages.append([
        "RESIDENTIAL LEASE AGREEMENT",
        "",
        "1. PARTIES AND PREMISES",
        f"This Residential Lease Agreement (\"Agreement\") is entered into between "
        f"{f['landlord']} (\"Landlord\") and {f['tenant']} (\"Tenant\").",
        f"1.2 Premises: The leased premises are located at {f['unit']}, "
        f"{f['city']}, {f['state']} (the \"Premises\").",
        "1.3 The Premises shall be used exclusively as a private residential dwelling and "
        "for no other purpose whatsoever.",
        "",
        "2. TERM OF LEASE",
        f"2.1 The term of this Agreement shall commence on {f['commence']} (\"Commencement Date\") "
        f"and shall continue for a period of {f['term_months']} months, expiring on {f['expire']} "
        "at 11:59 PM local time.",
        f"2.2 Tenant shall surrender possession of the Premises to Landlord on or before {f['expire']} "
        "unless this Agreement is renewed in writing.",
    ])

    # ---- Page 2: rent ------------------------------------------------------
    pages.append([
        "3. RENT",
        f"3.1 Monthly Rent: Tenant agrees to pay Landlord the sum of {money(r)} per month "
        "as base rent, payable in advance on or before the first (1st) day of each calendar month.",
        "3.2 Place of Payment: Rent shall be paid via the online tenant portal or by certified funds "
        "delivered to Landlord's management office.",
        f"3.3 Proration: If the Commencement Date falls after the first day of a month, the first "
        f"month's rent shall be prorated on a daily basis at 1/30th of {money(r)} per day.",
        "3.4 Rent is due in full regardless of whether Landlord provides a reminder, invoice, or statement.",
    ])

    # ---- Page 3: late fees, NSF -------------------------------------------
    pages.append([
        "4. LATE CHARGES AND RETURNED PAYMENTS",
        f"4.1 Grace Period: Rent received after the {f['grace_day']}th day of the month shall be "
        f"considered late and shall incur a one-time late charge of {money(f['late_fee'])}.",
        f"4.2 Additional Daily Charge: In addition to the late charge in Section 4.1, an additional "
        f"{money(f['daily_late_fee'])} per day shall accrue for each day rent remains unpaid after "
        f"the {f['grace_day']}th day.",
        f"4.3 Returned Payments: Any payment returned for insufficient funds shall incur a separate "
        f"service charge of {money(f['nsf_fee'])}, which is distinct from and in addition to any "
        "late charge assessed under Section 4.1.",
        "4.4 Late charges are considered additional rent and are collectible as such.",
    ])

    # ---- Page 4: security deposit -----------------------------------------
    pages.append([
        "5. SECURITY DEPOSIT",
        f"5.1 Amount: Upon execution of this Agreement, Tenant shall deposit with Landlord the sum of "
        f"{money(f['deposit'])} as a security deposit.",
        "5.2 The security deposit shall not be applied by Tenant as payment of the last month's rent "
        "or any other rent obligation during the term.",
        f"5.3 Return: Landlord shall return the security deposit, less any lawful deductions, within "
        f"{f['deposit_return_days']} days after Tenant vacates and returns all keys.",
        "5.4 Permitted Deductions: Landlord may deduct for unpaid rent, damage beyond ordinary wear "
        "and tear, cleaning necessary to restore the Premises, and unreturned keys or remotes.",
    ])

    # ---- Page 5: utilities -------------------------------------------------
    pages.append([
        "6. UTILITIES AND SERVICES",
        "6.1 Landlord's Responsibility: Landlord shall provide and pay for water, sewer, trash "
        "collection, and common area lighting.",
        "6.2 Tenant's Responsibility: Tenant shall establish accounts for and pay all charges for "
        "electricity, natural gas, internet, cable television, and telephone service.",
        "6.3 Tenant shall transfer all applicable utility accounts into Tenant's own name effective "
        "as of the Commencement Date and shall maintain them continuously through the term.",
        "6.4 Interruption: Landlord shall not be liable for interruption of any utility service "
        "arising from causes beyond Landlord's reasonable control.",
    ])

    # ---- Page 6: occupancy and guests -------------------------------------
    pages.append([
        "7. OCCUPANCY AND GUESTS",
        f"7.1 Permitted Occupants: The Premises shall be occupied by no more than "
        f"{f['max_occupants']} persons without Landlord's prior written consent.",
        f"7.2 Guests: Any guest remaining on the Premises for more than {f['guest_days']} consecutive "
        "days, or more than twice that number of days in any twelve-month period, shall be deemed an "
        "unauthorized occupant and requires Landlord's prior written authorization.",
        "7.3 Tenant is responsible for the conduct of all guests and invitees.",
        f"7.4 Quiet Hours: Quiet hours are observed daily from {f['quiet_start']} until 7:00 AM.",
    ])

    # ---- Page 7: pets ------------------------------------------------------
    pages.append([
        "8. PETS",
        "8.1 No animal, pet, or livestock of any kind shall be kept on the Premises without a "
        "separate signed Pet Addendum executed by Landlord.",
        f"8.2 Pet Deposit: A refundable pet deposit of {money(f['pet_deposit'])} is required per "
        "approved animal at the time the Pet Addendum is signed.",
        f"8.3 Pet Rent: In addition to the pet deposit, monthly pet rent of {money(f['pet_rent'])} "
        "per approved animal shall be added to the base rent and is due with each rent payment.",
        f"8.4 Restrictions: No individual animal may exceed {f['pet_weight']} pounds at maturity. "
        "Service animals and assistance animals required by applicable fair housing law are exempt "
        "from the deposit, pet rent, and weight restrictions in this Section.",
    ])

    # ---- Page 8: maintenance ----------------------------------------------
    pages.append([
        "9. MAINTENANCE AND REPAIRS",
        "9.1 Landlord's Duties: Landlord shall maintain the structural elements, roof, plumbing, "
        "electrical systems, and heating equipment in good and safe working order.",
        "9.2 Tenant's Duties: Tenant shall keep the Premises clean and sanitary, dispose of refuse "
        "properly, and promptly report any condition requiring repair.",
        f"9.3 Smoke Detectors: Tenant shall test all smoke and carbon monoxide detectors monthly and "
        f"shall report any non-functioning detector to Landlord within {f['smoke_detector_days']} days.",
        f"9.4 Keys: A charge of {money(f['key_replacement_fee'])} per key shall apply to replace any "
        "lost key, fob, or remote control device.",
        "9.5 Tenant shall not perform any repair for which Tenant intends to seek reimbursement "
        "without Landlord's prior written approval of the estimated cost.",
    ])

    # ---- Page 9: alterations, entry ---------------------------------------
    pages.append([
        "10. ALTERATIONS",
        "10.1 Tenant shall not paint, wallpaper, install fixtures, change locks, or make any "
        "structural alteration to the Premises without Landlord's express prior written consent.",
        "10.2 Any alteration made without consent shall be restored at Tenant's expense.",
        "",
        "11. RIGHT OF ENTRY",
        "11.1 Landlord and Landlord's authorized agents may enter the Premises to inspect, make "
        "repairs, or show the unit to prospective tenants or purchasers.",
        f"11.2 Notice: Except in an emergency involving imminent hazard to person or property, "
        f"Landlord shall provide Tenant with at least {f['entry_notice_hours']} hours advance notice "
        "before entering the Premises.",
        "11.3 Entry shall occur during reasonable hours except in the case of emergency.",
    ])

    # ---- Page 10: sublet, assignment --------------------------------------
    pages.append([
        "12. ASSIGNMENT AND SUBLETTING",
        "12.1 Tenant shall not assign this Agreement, sublet the Premises in whole or in part, or "
        "list the Premises on any short-term rental platform without Landlord's prior written consent.",
        "12.2 Any purported assignment or sublease made without such consent shall be void and shall "
        "constitute a material breach of this Agreement.",
        "12.3 Landlord's consent to one assignment or sublease shall not waive the requirement of "
        "consent for any subsequent assignment or sublease.",
    ])

    # ---- Page 11: early termination ---------------------------------------
    early_fee = r * f["early_termination_months"]
    pages.append([
        "13. EARLY TERMINATION",
        f"13.1 Notice: Tenant may terminate this Agreement prior to the expiration date by delivering "
        f"written notice to Landlord at least {f['termination_notice_days']} days in advance.",
        f"13.2 Termination Fee: In addition to the notice required in Section 13.1, Tenant shall pay "
        f"an early termination fee equal to {f['early_termination_months']} month(s) of base rent, "
        f"being {money(early_fee)}.",
        "13.3 Military Clause: Tenant may terminate this Agreement without penalty pursuant to the "
        "Servicemembers Civil Relief Act upon receipt of qualifying military orders, with a copy of "
        "such orders delivered to Landlord.",
        "13.4 Tenant remains liable for all rent and charges accrued through the termination date.",
    ])

    # ---- Page 12: renewal, holdover ---------------------------------------
    holdover_rent = int(r * f["holdover_multiplier"] / 100)
    pages.append([
        "14. RENEWAL AND HOLDOVER",
        f"14.1 Renewal: Either party may elect not to renew by delivering written notice at least "
        f"{f['termination_notice_days']} days before the expiration date.",
        "14.2 Absent such notice, this Agreement shall convert to a month-to-month tenancy upon "
        "expiration, subject to all other terms and conditions herein.",
        f"14.3 Holdover: If Tenant remains in possession after expiration without Landlord's written "
        f"consent, Tenant shall pay holdover rent equal to {f['holdover_multiplier']}% of the base "
        f"monthly rent, being {money(holdover_rent)} per month.",
    ])

    # ---- Page 13: default, insurance --------------------------------------
    pages.append([
        "15. DEFAULT AND REMEDIES",
        "15.1 Tenant's failure to comply with any material provision of this Agreement shall "
        "constitute an event of default.",
        f"15.2 Cure Period: Upon default, Landlord shall deliver written notice specifying the "
        f"default, and Tenant shall have {f['cure_days']} days from delivery of such notice to cure "
        "the default or vacate the Premises.",
        "15.3 Remedies: Upon an uncured default, Landlord may pursue all remedies available at law "
        "or in equity, including termination of tenancy and recovery of possession.",
        "",
        "16. INSURANCE",
        f"16.1 Tenant shall obtain and maintain renter's liability insurance with minimum coverage "
        f"of {money(f['insurance_coverage'])} for the duration of the tenancy.",
        "16.2 Tenant shall name Landlord as an interested party and furnish proof of coverage upon "
        "request. Landlord's insurance does not cover Tenant's personal property.",
    ])

    # ---- Page 14: parking, governing law ----------------------------------
    parking_text = (
        f"17.2 Parking Fee: A monthly parking fee of {money(f['parking_fee'])} per space shall be "
        "added to the base rent."
        if f["parking_fee"] else
        "17.2 Parking Fee: Assigned parking is provided at no additional charge to Tenant."
    )
    pages.append([
        "17. PARKING",
        f"17.1 Assigned Spaces: Tenant is assigned {f['parking_spaces']} parking space(s) for the "
        "duration of the tenancy.",
        parking_text,
        "17.3 Vehicles that are inoperable, unregistered, or leaking fluids may be towed at the "
        "vehicle owner's expense after 72 hours' notice.",
        "",
        "18. GOVERNING LAW",
        f"18.1 This Agreement shall be governed by and construed in accordance with the laws of the "
        f"State of {f['state']}.",
        "18.2 Entire Agreement: This document constitutes the entire agreement between the parties "
        "and supersedes all prior negotiations, representations, or agreements.",
    ])

    # Pad every substantive page with boilerplate so pages are realistically dense
    # and a page yields more than one retrievable chunk.
    pages = [pad(prng, p, 12) for p in pages]

    # ---- Distractor pages --------------------------------------------------
    # A summary fee schedule that repeats similar dollar amounts in a different
    # context, plus an addendum page. These exist to punish naive keyword or
    # naive vector matching: they look highly relevant to money questions but
    # are never the authoritative clause.
    pages.append(pad(prng, [
        "EXHIBIT A — SCHEDULE OF ANCILLARY CHARGES",
        "The following schedule is provided for informational convenience only. In the event of any "
        "conflict between this Exhibit and the body of the Agreement, the body of the Agreement "
        "controls.",
        f"Application processing charge: {money(rng_pick(prng, [40, 55, 65]))} per adult applicant.",
        f"Month-to-month premium, if applicable: {money(rng_pick(prng, [95, 150, 200]))} per month.",
        f"Common area maintenance assessment: {money(rng_pick(prng, [15, 25, 40]))} per month.",
        f"Lock-out service call during business hours: {money(rng_pick(prng, [35, 55, 75]))}.",
        f"Unauthorized vehicle towing administrative charge: {money(rng_pick(prng, [50, 85, 110]))}.",
        f"Late payment of ancillary charges: {money(rng_pick(prng, [20, 30, 45]))} per occurrence.",
        "Charges listed above are additional rent and are due with the next monthly rent payment.",
    ], 4))

    pages.append(pad(prng, [
        "EXHIBIT B — MOVE-IN CONDITION AND MAINTENANCE ADDENDUM",
        "Tenant shall complete and return the move-in condition checklist within seventy-two hours of "
        "taking possession. Items not noted are presumed to be in good condition.",
        "Routine maintenance requests shall be submitted through the online portal. Emergency "
        "maintenance involving fire, flood, gas odor, or loss of heat shall be reported by telephone.",
        "Tenant shall replace furnace filters quarterly and shall not dispose of grease, wipes, or "
        "fibrous material in any drain or toilet.",
        "Landlord shall respond to non-emergency maintenance requests within a commercially "
        "reasonable period, ordinarily not exceeding five business days.",
        "Seasonal inspections of smoke detectors, water heaters, and HVAC equipment may be conducted "
        "with proper advance notice as set forth in the Agreement.",
    ], 5))

    return [
        {"page_num": i + 1, "text": "\n".join(lines)}
        for i, lines in enumerate(pages)
    ]


def rng_pick(rng: random.Random, options: list[int]) -> int:
    return rng.choice(options)


def build_questions(f: dict, pages: list[dict]) -> list[dict]:
    """
    Derive QA pairs from the recorded facts.

    Each item carries:
      answer_keys  - strings that MUST appear in a correct answer (deterministic check)
      gold_page    - the page the supporting clause lives on (citation check)
      gold_section - the clause id, used to locate the gold chunk for retrieval scoring
      category     - lookup | multi_hop | adversarial | unanswerable
    """
    r = f["rent"]
    early_fee = r * f["early_termination_months"]
    holdover_rent = int(r * f["holdover_multiplier"] / 100)
    first_month = r + f["deposit"]
    rent_with_pet = r + f["pet_rent"]
    late_total = r + f["late_fee"]

    def q(question, keys, page, section, category):
        return {
            "question": question,
            "answer_keys": keys if isinstance(keys, list) else [keys],
            "gold_page": page,
            "gold_section": section,
            "category": category,
        }

    items = [
        # ---- direct lookup -------------------------------------------------
        q("What is the monthly base rent?", money(r), 2, "3.1", "lookup"),
        q("When is rent due each month?", ["first", "1st"], 2, "3.1", "lookup"),
        q("How much is the security deposit?", money(f["deposit"]), 4, "5.1", "lookup"),
        q("How many days does the landlord have to return my security deposit?",
          str(f["deposit_return_days"]), 4, "5.3", "lookup"),
        q("When does the lease expire?", f["expire"], 1, "2.1", "lookup"),
        q("How long is the lease term?", str(f["term_months"]), 1, "2.1", "lookup"),
        q("What is the late fee for paying rent late?", money(f["late_fee"]), 3, "4.1", "lookup"),
        q("How much notice must the landlord give before entering?",
          str(f["entry_notice_hours"]), 9, "11.2", "lookup"),
        q("How many people are allowed to live in the unit?",
          str(f["max_occupants"]), 6, "7.1", "lookup"),
        q("How much is the pet deposit?", money(f["pet_deposit"]), 7, "8.2", "lookup"),
        q("What is the maximum weight allowed for a pet?", str(f["pet_weight"]), 7, "8.4", "lookup"),
        q("How much renter's insurance coverage am I required to carry?",
          money(f["insurance_coverage"]), 13, "16.1", "lookup"),
        q("How many parking spaces am I assigned?", str(f["parking_spaces"]), 14, "17.1", "lookup"),
        q("Which state's law governs this lease?", f["state"], 14, "18.1", "lookup"),
        q("How many days do I have to cure a default?", str(f["cure_days"]), 13, "15.2", "lookup"),
        q("How much notice do I need to give to terminate early?",
          str(f["termination_notice_days"]), 11, "13.1", "lookup"),
        q("Who pays for the internet?", "Tenant", 5, "6.2", "lookup"),
        q("Who pays for water and trash?", "Landlord", 5, "6.1", "lookup"),
        q("What is the charge to replace a lost key?",
          money(f["key_replacement_fee"]), 8, "9.4", "lookup"),
        q("When do quiet hours start?", f["quiet_start"], 6, "7.4", "lookup"),

        # ---- multi-hop: needs two clauses combined -------------------------
        q(f"If I pay rent on the {f['grace_day'] + 3}th of the month, how much do I owe in total?",
          [money(late_total)], 3, "3.1+4.1", "multi_hop"),
        q("What is my total due at move-in, counting first month's rent and the deposit?",
          money(first_month), 4, "3.1+5.1", "multi_hop"),
        q("If I get an approved dog, what is my total monthly payment?",
          money(rent_with_pet), 7, "3.1+8.3", "multi_hop"),
        q("What is the total early termination fee in dollars?",
          money(early_fee), 11, "13.2", "multi_hop"),
        q("If I stay past the expiration date without consent, what is the monthly rent?",
          money(holdover_rent), 12, "14.3", "multi_hop"),
        q("Can I have a guest stay for a full month without asking the landlord?",
          ["No", "no"], 6, "7.2", "multi_hop"),

        # ---- adversarial: a confusable clause sits nearby ------------------
        q("How much is the returned check fee, not the late fee?",
          money(f["nsf_fee"]), 3, "4.3", "adversarial"),
        q("What is the monthly pet rent, as opposed to the pet deposit?",
          money(f["pet_rent"]), 7, "8.3", "adversarial"),
        q("Besides the one-time late charge, what is the additional daily charge for unpaid rent?",
          money(f["daily_late_fee"]), 3, "4.2", "adversarial"),
        q("Can I list the apartment on Airbnb?", ["No", "no", "not"], 10, "12.1", "adversarial"),
        q("Do I have to pay a pet deposit for a service animal?",
          ["No", "exempt", "not"], 7, "8.4", "adversarial"),
        q("Can I use the security deposit to pay my last month of rent?",
          ["No", "not", "shall not"], 4, "5.2", "adversarial"),
        q("Can I change the locks myself?", ["No", "not", "consent"], 9, "10.1", "adversarial"),

        # ---- unanswerable: correct behavior is an explicit refusal ---------
        q("What is the landlord's mobile phone number?", ["cannot find"], -1, "none", "unanswerable"),
        q("Does the building have a swimming pool or fitness center?", ["cannot find"], -1, "none", "unanswerable"),
        q("What happens to the lease if there is an earthquake?", ["cannot find"], -1, "none", "unanswerable"),
        q("How much did the landlord pay for this property?", ["cannot find"], -1, "none", "unanswerable"),
    ]

    # Index every numbered clause to the page it appears on, so gold pages and
    # gold clause text are derived from the rendered document rather than guessed.
    section_page: dict[str, int] = {}
    section_text: dict[str, str] = {}
    for page in pages:
        for line in page["text"].split("\n"):
            stripped = line.strip()
            head = stripped.split(" ")[0].rstrip(":")
            if head and head[0].isdigit() and "." in head and head not in section_page:
                section_page[head] = page["page_num"]
                section_text[head] = stripped

    for item in items:
        item["lease_index"] = f["lease_index"]
        sections = [s for s in item["gold_section"].split("+") if s != "none"]
        pages_needed = sorted({section_page[s] for s in sections if s in section_page})
        item["gold_pages"] = pages_needed
        item["gold_clauses"] = [section_text[s] for s in sections if s in section_text]
        item["gold_clause"] = item["gold_clauses"][0] if item["gold_clauses"] else ""
        # keep the primary page consistent with what the document actually says
        if pages_needed:
            item["gold_page"] = pages_needed[0]
    return items


def main() -> None:
    rng = random.Random(SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    corpus = []
    dataset = []

    for idx in range(NUM_LEASES):
        facts = make_facts(rng, idx)
        pages = build_pages(facts)
        questions = build_questions(facts, pages)

        corpus.append({
            "lease_index": idx,
            "title": f"Residential Lease — {facts['unit']}",
            "facts": facts,
            "pages": pages,
        })
        dataset.extend(questions)

    (DATA_DIR / "corpus.json").write_text(json.dumps(corpus, indent=2), encoding="utf-8")
    (DATA_DIR / "golden_qa_large.json").write_text(json.dumps(dataset, indent=2), encoding="utf-8")

    by_cat: dict[str, int] = {}
    for item in dataset:
        by_cat[item["category"]] = by_cat.get(item["category"], 0) + 1

    total_pages = sum(len(c["pages"]) for c in corpus)
    total_words = sum(len(p["text"].split()) for c in corpus for p in c["pages"])

    print(f"Corpus:   {len(corpus)} leases, {total_pages} pages, {total_words:,} words")
    print(f"Dataset:  {len(dataset)} questions")
    for cat, n in sorted(by_cat.items()):
        print(f"            {cat:<14} {n}")
    print(f"Written to {DATA_DIR}")


if __name__ == "__main__":
    main()
