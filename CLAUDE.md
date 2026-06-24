# Danielle "Danni" Adams — Profile & Project Context

## PRIMARY MONEY TRACK — Nonprofit Consulting Emails (APPROVED JUNE 2026)

The nonprofit profile is the #1 revenue priority. Danni pitches herself as a communications consultant to nonprofits. These emails are APPROVED and FINAL. Do not rewrite without explicit instruction.

**Sends from:** hello@danniadams.me
**Profile key in CSV:** nonprofit
**Signature:** Name + hello@danniadams.me only. No Instagram. No @amapoundcake.
**Calendly:** Must always be a hyperlink with human link text (e.g. "Grab time here."). Never paste the raw URL as visible text.

**Rules that are non-negotiable for ALL emails:**
- No em dashes
- No double dashes (--)
- No phrases like "Not generic. Specific to what you're doing." (reads as AI)
- No @amapoundcake in nonprofit/consulting signature (she is in lingerie on that page)

**Approved email structure:**
1. Intro: Orlando-based communications consultant, MPA from UNF, former Senior Project Manager and Strategic Partnerships
2. Credibility: Institute for Body Image, donor visibility work, digital campaigns, "I know what it takes to reach people when you don't have a big team behind you"
3. Offer: fractional strategic partner, grow supporter base, community relationships funders care about, outreach systems without adding to staff load
4. Hook: specific ideas for their org around storytelling, visibility, and outreach
5. CTA: 20-minute call, hyperlinked Calendly



## Who She Is
Danielle Leona Adams, known professionally as **Danni Adams** and by her brand name **Ama Pound Cake**, is an Orlando-based actress, media personality, social media influencer, speaker, educator, and body image advocate.

## Contact
- Email: amapoundcake@gmail.com
- Phone: 407-430-9458
- Location: Orlando, FL (available nationally and internationally)
- Website: www.amapoundcake.com (currently down — renewing Friday)
- Instagram: @amapoundcake (52.5K followers)
- TikTok: @amapoundcake (11.4K followers)
- Engagement rate: 4% average (industry average is 1-3%)
- Audience: 74% women, 26% men, ages 25-54
- Top markets: Orlando, Atlanta, Miami, NYC

## Three Professional Tracks

### 1. Entertainment & Brand (email: amapoundcake@gmail.com)
Actress, on-camera talent, host, and brand partner.

**Television**
- Cracked Addicts (2024) | Featured | TLC
- The Jennifer Hudson Show | Featured | Warner Bros. Television
- Tamron Hall Show | Featured | ABC
- The People's Court | Featured | Syndicated
- Fox News | Appearance
- Dr. Phil | Appearance

**Commercial**
- Leach Law Firm (2025) | Principal | Regional
- T-Mobile (2026) | Background | National
- Sixt (2026) | Principal | National

**Theater**
- Stage Struck (Upcoming) | Sam | Lake Nona Arts
- Unshakable Faith | Ensemble, First Lady Understudy
- I Love the 80s | Bertha | American Immersive Theater

**Music Video**
- Romeo Santos | Dancer / Background | Sony Music (4+ billion streams artist)

**Modeling**
- Vogue Editorial Feature | Editorial
- The Cut Editorial | Editorial
- Miami Swim Week

**Hosting**
- Social Icon Influencer Conference | Host
- BET Beauty Brunch | Host

**Brand Partnerships**
YITTY by Lizzo/Fabletics, T-Mobile, Hilton Hotels, Sixt, Morphe Beauty, BH Cosmetics, Chromat, ELOQUII, Fashion to Figure, Uniquely Vintage, Curvy Sense, Alpine Butterfly Swim, Modcloth

**Skills**
Accents: Southern, American, Irish | Improv | Dancing: Hip Hop, Freestyle, Salsa, Bachata | Voice: Alto | Costume Design & Props | Singing

### 2. Speaker & Educator (email: amapoundcake@gmail.com — speak@ when domain renews)
Speaker on social media, storytelling, representation, body image, and personal resilience.

**Speaking Topics**
1. Rewriting the Algorithm — social media, culture, identity, intention
2. Nobody Is Coming to Save You — building a career/brand/platform without an agent, cosign, or permission
3. Beauty, Bodies, and the Stories We're Sold — beauty standards, who profits, media literacy
4. Building Communities That Last — followers vs. belonging, real movements
5. Perseverance, Grace & Growth — not giving up, hard things happen, self-confidence, dreaming big (delivered at Seminole Leadership Conference and girls' mentoring/shelter programs)

**Past Engagements**
- Harvard University
- University of Ottawa
- Full Sail University
- Bethune-Cookman University
- Seminole Leadership Conference | Keynote | Perseverance, Grace & Growth
- Social Icon Influencer Conference | Host
- BET Beauty Brunch | Host
- Women's shelters (ongoing) | Talk: not giving up, self-confidence, dream big
- Girls' mentoring programs (ongoing) | Talk: not giving up, self-confidence, dream big

**Credentials**
- Nonprofit Leader Award — Central Florida
- Co-Creator, Institute for Body Image (trains medical professionals in inclusive, body-positive care)

### 3. Social Media Influencer / Brand Partnerships
Platform: @amapoundcake
Niche: Plus-size fashion, beauty, body image, inclusive representation
Tagline: "She is the audience you've been trying to reach."

## What Makes Her Uniquely Positioned
She is a social media influencer who speaks at Harvard AND walks into women's shelters and girls' mentoring programs. Her representation work is not aesthetic — it is lived. This combination (Vogue + Harvard + women's shelters + national TV + brand deals) is extremely rare and is her core differentiator.

## Key Organizations She Founded/Co-Founded
- **Institute for Body Image** — professional development program training medical providers in inclusive, body-positive care (active)
- **Shyne Wayv** — currently down/inactive

## Current Project: Outreach Automation (this repo)
This repo contains an automated lead generation and cold email system. The system needs to be updated to support two outreach profiles:
- Profile 1: Entertainment & Brand — targeting talent agencies, casting directors, brands, PR firms
- Profile 2: Speaker/Educator — targeting universities, conferences, corporate DEI programs, nonprofits

## Files in This Repo
- `main.py` — orchestrator (daily / followup / status commands)
- `lead_finder.py` — scrapes Idealist, Chamber of Commerce, GuideStar, Google Maps, manual CSV
- `email_templates.py` — templates for initial, followup, and check-in emails (has Claude API stub)
- `email_sender.py` — Gmail SMTP sender
- `sheets_logger.py` — Google Sheets logging
- `config.py` — configuration and env vars
- `speaker_media_kit.html` — Danni's speaker one-sheet (Boz-approved copy)
- `brand_media_kit.html` — Danni's brand/influencer media kit (Boz-approved copy)
- `danni_photo.jpeg` — her photo (used in brand kit hero)

## Pending To-Dos
- [ ] Build two-profile outreach system (speaker profile + entertainment/brand profile)
- [ ] Fix two bugs in lead_finder.py (lines 298, 366 — undefined CHAMBER_URL and CANDID_URL variables)
- [ ] Add speak@amapoundcake.com email when domain renews Friday
- [ ] Get formal Hilton testimonial quote (he said she was "a pleasure to work with")
- [ ] Add Calendly link to both kits once set up
- [ ] Add women's shelter / girls' mentoring program work to both kits
- [ ] Activate Claude API email personalization (stub already in email_templates.py)

## Tech Stack (as of June 18, 2026)

### Domain & Email
- Domain: **danniadams.me** (active on Namecheap)
- Inboxes (Namecheap Private Email): hello@danniadams.me, partnerships@danniadams.me, speaking@danniadams.me
- Primary sending address: hello@danniadams.me

### Email Sending
- **Brevo** — account under hello@danniadams.me, domain fully authenticated (DKIM, DMARC, SPF all configured)

### Storage & Docs
- **Notion** — primary workspace, MCP connected
- **Google Drive** — MCP connected

### Scheduling & Comms
- **Calendly** — set up and active
- **Slack** — connected to Claude

### Active MCP Integrations
- Notion, Google Drive, Brevo, Gmail, Google Calendar, Slack

### Email Warm-Up Strategy
- Start with own inboxes (hello@, partnerships@, speaking@), then warm contacts, then past brand partners, then cold outreach
- Ramp: 20-30 emails/day, increase ~20%/week
- Always use random send delay (30-90 seconds between sends) in email_sender.py

## Voice & Tone Notes
- She does NOT want AI-coded corporate language
- Reference voice: Keke Palmer (real, no-nonsense, culturally aware) + Call Her Daddy (direct, honest)
- Speaker kit copy reference: Bozoma Saint John (bold, strategic, CMO-level positioning)
- No em dashes in any of her documents
- No links to amapoundcake.com until domain is renewed
