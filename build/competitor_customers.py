"""
Per-vendor named-customer references — seeded demo dataset.

This is illustrative seed data, not a comprehensive customer list. Vendors
generally do not publish full customer rosters. Replace by wiring scrapers
for each vendor's case-study / customer-logo pages (see fetch hints below).

Each record:
    vendor:    vendor name (must match COMPETITORS key in competitors.py)
    muni:      municipality / county / SD name
    state:     2-letter state code
    type:      "muni" | "county" | "township" | "special_district"
    bucket:    population bucket (or None)
    product:   product line installed (vendor-specific module)
    since:     approximate go-live year (best-effort)
    source:    where the reference was sighted (e.g., vendor case study)
    demo:      True until replaced with verified data

# refreshed 2026-05-01
"""


# --- Sourcing hints for each vendor --------------------------------------
# Wire these into a real scraper to replace the seed data:
#
#   Tyler Technologies — https://www.tylertech.com/case-studies
#                        https://www.tylertech.com/about-us/customer-stories
#   BS&A Software      — https://www.bsasoftware.com/customer-success-stories
#   Caselle            — https://caselle.com/about-us/customers
#   gWorks             — https://www.gworks.com/customers
#   Muni-Link          — https://www.muni-link.com/customers
#   TownCloud          — https://www.towncloud.com/case-studies
#
# Also useful:
#   - G2 / Capterra customer-logo pages
#   - LinkedIn company "people work at" filter
#   - State municipal-league directories cross-referenced with vendor logos
#   - Public RFP responses (vendor wins/losses by state)


CUSTOMERS = [
    # ============== Tyler Technologies ==============
    # Tyler's named references span enterprise ERP (Munis / Enterprise),
    # public safety (New World, Brazos), courts, and payments (NIC).
    {"vendor": "Tyler Technologies", "muni": "Plano",          "state": "TX", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2014, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Frisco",         "state": "TX", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2017, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Arlington",      "state": "TX", "type": "muni",   "bucket": "100K+",   "product": "Public Safety",   "since": 2016, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Wake County",    "state": "NC", "type": "county", "bucket": "100K+",   "product": "Odyssey Courts",  "since": 2015, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Mecklenburg County","state": "NC","type":"county","bucket":"100K+",   "product": "Munis ERP",       "since": 2012, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Sacramento",     "state": "CA", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2013, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Long Beach",     "state": "CA", "type": "muni",   "bucket": "100K+",   "product": "Public Safety",   "since": 2018, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Cook County",    "state": "IL", "type": "county", "bucket": "100K+",   "product": "Odyssey Courts",  "since": 2017, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Chicago",        "state": "IL", "type": "muni",   "bucket": "100K+",   "product": "Public Safety",   "since": 2014, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Anchorage",      "state": "AK", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2011, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Boston",         "state": "MA", "type": "muni",   "bucket": "100K+",   "product": "MUNIS Enterprise","since": 2008, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Tampa",          "state": "FL", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2016, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Hillsborough County","state":"FL","type":"county","bucket":"100K+",   "product": "Odyssey Courts",  "since": 2013, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Salt Lake City", "state": "UT", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2012, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Denver",         "state": "CO", "type": "muni",   "bucket": "100K+",   "product": "Public Safety",   "since": 2015, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Aurora",         "state": "CO", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2017, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Portland",       "state": "OR", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2010, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Knoxville",      "state": "TN", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2014, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Nashville",      "state": "TN", "type": "muni",   "bucket": "100K+",   "product": "Public Safety",   "since": 2016, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Charleston County","state":"SC","type":"county","bucket":"100K+",     "product": "Odyssey Courts",  "since": 2018, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Henrico County", "state": "VA", "type": "county", "bucket": "100K+",   "product": "Munis ERP",       "since": 2009, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Loudoun County", "state": "VA", "type": "county", "bucket": "100K+",   "product": "Munis ERP",       "since": 2015, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Albuquerque",    "state": "NM", "type": "muni",   "bucket": "100K+",   "product": "Public Safety",   "since": 2013, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Phoenix",        "state": "AZ", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2007, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Tucson",         "state": "AZ", "type": "muni",   "bucket": "100K+",   "product": "Public Safety",   "since": 2017, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Spokane",        "state": "WA", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2015, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Seattle",        "state": "WA", "type": "muni",   "bucket": "100K+",   "product": "Public Safety",   "since": 2016, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Des Moines",     "state": "IA", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2012, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Omaha",          "state": "NE", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2014, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Baton Rouge",    "state": "LA", "type": "muni",   "bucket": "100K+",   "product": "Public Safety",   "since": 2011, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Louisville",     "state": "KY", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2013, "source": "Tyler case study", "demo": True},
    {"vendor": "Tyler Technologies", "muni": "Pittsburgh",     "state": "PA", "type": "muni",   "bucket": "100K+",   "product": "Munis ERP",       "since": 2014, "source": "Tyler case study", "demo": True},

    # ============== BS&A Software ==============
    # MI dominant. Acquired by Harris/Constellation 2021.
    {"vendor": "BS&A Software", "muni": "Grand Rapids",   "state": "MI", "type": "muni",   "bucket": "100K+",   "product": "Financial Mgmt",  "since": 2010, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Lansing",        "state": "MI", "type": "muni",   "bucket": "100K+",   "product": "Financial Mgmt",  "since": 2012, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Ann Arbor",      "state": "MI", "type": "muni",   "bucket": "100K+",   "product": "Financial + Tax", "since": 2009, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Kalamazoo",      "state": "MI", "type": "muni",   "bucket": "50K-100K","product": "Financial Mgmt",  "since": 2014, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Saginaw",        "state": "MI", "type": "muni",   "bucket": "20K-50K", "product": "Financial Mgmt",  "since": 2008, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Bay City",       "state": "MI", "type": "muni",   "bucket": "20K-50K", "product": "Financial + Tax", "since": 2010, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Battle Creek",   "state": "MI", "type": "muni",   "bucket": "20K-50K", "product": "Financial Mgmt",  "since": 2011, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Midland",        "state": "MI", "type": "muni",   "bucket": "20K-50K", "product": "Financial + Tax", "since": 2013, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Holland",        "state": "MI", "type": "muni",   "bucket": "20K-50K", "product": "Financial Mgmt",  "since": 2015, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Marquette",      "state": "MI", "type": "muni",   "bucket": "20K-50K", "product": "Financial Mgmt",  "since": 2014, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Traverse City",  "state": "MI", "type": "muni",   "bucket": "10K-20K", "product": "Financial + Tax", "since": 2009, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Mt. Pleasant",   "state": "MI", "type": "muni",   "bucket": "20K-50K", "product": "Financial Mgmt",  "since": 2016, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Plymouth",       "state": "MI", "type": "muni",   "bucket": "5K-10K",  "product": "Financial Mgmt",  "since": 2012, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Royal Oak",      "state": "MI", "type": "muni",   "bucket": "50K-100K","product": "Financial + Tax", "since": 2010, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Troy",           "state": "MI", "type": "muni",   "bucket": "50K-100K","product": "Financial Mgmt",  "since": 2008, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Livonia",        "state": "MI", "type": "muni",   "bucket": "50K-100K","product": "Financial Mgmt",  "since": 2009, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Sterling Heights","state": "MI","type": "muni",   "bucket": "100K+",   "product": "Financial Mgmt",  "since": 2007, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Warren",         "state": "MI", "type": "muni",   "bucket": "100K+",   "product": "Financial + Tax", "since": 2011, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Dearborn",       "state": "MI", "type": "muni",   "bucket": "50K-100K","product": "Financial Mgmt",  "since": 2013, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Toledo",         "state": "OH", "type": "muni",   "bucket": "100K+",   "product": "Financial Mgmt",  "since": 2018, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Findlay",        "state": "OH", "type": "muni",   "bucket": "20K-50K", "product": "Financial Mgmt",  "since": 2019, "source": "BS&A case study", "demo": True},
    {"vendor": "BS&A Software", "muni": "Fort Wayne",     "state": "IN", "type": "muni",   "bucket": "100K+",   "product": "Financial Mgmt",  "since": 2020, "source": "BS&A case study", "demo": True},

    # ============== Caselle ==============
    # Mountain West stronghold; small towns.
    {"vendor": "Caselle", "muni": "Provo",        "state": "UT", "type": "muni", "bucket": "100K+",  "product": "Caselle Connect",  "since": 2007, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Logan",        "state": "UT", "type": "muni", "bucket": "50K-100K","product": "Caselle Connect", "since": 2010, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Ogden",        "state": "UT", "type": "muni", "bucket": "50K-100K","product": "Caselle Connect", "since": 2009, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "St. George",   "state": "UT", "type": "muni", "bucket": "50K-100K","product": "Financials",      "since": 2013, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Lehi",         "state": "UT", "type": "muni", "bucket": "50K-100K","product": "Caselle Connect", "since": 2015, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Cedar City",   "state": "UT", "type": "muni", "bucket": "20K-50K", "product": "Caselle Connect", "since": 2012, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Idaho Falls",  "state": "ID", "type": "muni", "bucket": "50K-100K","product": "Caselle Connect", "since": 2008, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Pocatello",    "state": "ID", "type": "muni", "bucket": "50K-100K","product": "Caselle Connect", "since": 2010, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Twin Falls",   "state": "ID", "type": "muni", "bucket": "20K-50K", "product": "Caselle Connect", "since": 2011, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Coeur d'Alene","state": "ID", "type": "muni", "bucket": "50K-100K","product": "Caselle Connect", "since": 2014, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Bozeman",      "state": "MT", "type": "muni", "bucket": "50K-100K","product": "Caselle Connect", "since": 2009, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Billings",     "state": "MT", "type": "muni", "bucket": "100K+",   "product": "Caselle Connect", "since": 2007, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Great Falls",  "state": "MT", "type": "muni", "bucket": "50K-100K","product": "Caselle Connect", "since": 2008, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Helena",       "state": "MT", "type": "muni", "bucket": "20K-50K", "product": "Caselle Connect", "since": 2012, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Casper",       "state": "WY", "type": "muni", "bucket": "50K-100K","product": "Caselle Connect", "since": 2010, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Cheyenne",     "state": "WY", "type": "muni", "bucket": "50K-100K","product": "Caselle Connect", "since": 2009, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Laramie",      "state": "WY", "type": "muni", "bucket": "20K-50K", "product": "Caselle Connect", "since": 2013, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Reno",         "state": "NV", "type": "muni", "bucket": "100K+",   "product": "Caselle Connect", "since": 2011, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Carson City",  "state": "NV", "type": "muni", "bucket": "50K-100K","product": "Caselle Connect", "since": 2008, "source": "Caselle case study", "demo": True},
    {"vendor": "Caselle", "muni": "Elko",         "state": "NV", "type": "muni", "bucket": "10K-20K", "product": "Caselle Connect", "since": 2014, "source": "Caselle case study", "demo": True},

    # ============== gWorks ==============
    # Plains-states stronghold; very small towns; roll-up of acquisitions.
    {"vendor": "gWorks", "muni": "Norfolk",       "state": "NE", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2015, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Grand Island",  "state": "NE", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2016, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Kearney",       "state": "NE", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2017, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Fremont",       "state": "NE", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2014, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Hastings",      "state": "NE", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2018, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Beatrice",      "state": "NE", "type": "muni", "bucket": "10K-20K", "product": "gWorks Suite",  "since": 2016, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Aberdeen",      "state": "SD", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2017, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Mitchell",      "state": "SD", "type": "muni", "bucket": "10K-20K", "product": "gWorks Suite",  "since": 2018, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Brookings",     "state": "SD", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2019, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Spearfish",     "state": "SD", "type": "muni", "bucket": "10K-20K", "product": "gWorks Suite",  "since": 2017, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Bismarck",      "state": "ND", "type": "muni", "bucket": "50K-100K","product": "gWorks GIS",    "since": 2019, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Minot",         "state": "ND", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2018, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Mason City",    "state": "IA", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2017, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Marshalltown",  "state": "IA", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2016, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Ottumwa",       "state": "IA", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2018, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Salina",        "state": "KS", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2017, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Hutchinson",    "state": "KS", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2018, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Garden City",   "state": "KS", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2019, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "Jefferson City","state": "MO", "type": "muni", "bucket": "20K-50K", "product": "gWorks Suite",  "since": 2020, "source": "gWorks case study", "demo": True},
    {"vendor": "gWorks", "muni": "St. Joseph",    "state": "MO", "type": "muni", "bucket": "50K-100K","product": "gWorks GIS",    "since": 2018, "source": "gWorks case study", "demo": True},

    # ============== Muni-Link ==============
    # Utility-billing pure-play; PA/OH/WV concentrated.
    {"vendor": "Muni-Link", "muni": "Erie",          "state": "PA", "type": "muni", "bucket": "50K-100K","product": "Utility Billing", "since": 2016, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Allentown",     "state": "PA", "type": "muni", "bucket": "100K+",   "product": "Utility Billing", "since": 2018, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Bethlehem",     "state": "PA", "type": "muni", "bucket": "50K-100K","product": "Utility Billing", "since": 2017, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Reading",       "state": "PA", "type": "muni", "bucket": "50K-100K","product": "Utility Billing", "since": 2019, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Lancaster",     "state": "PA", "type": "muni", "bucket": "50K-100K","product": "Utility Billing", "since": 2015, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Harrisburg",    "state": "PA", "type": "muni", "bucket": "20K-50K", "product": "Utility Billing", "since": 2016, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Altoona",       "state": "PA", "type": "muni", "bucket": "20K-50K", "product": "Utility Billing", "since": 2018, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Akron",         "state": "OH", "type": "muni", "bucket": "100K+",   "product": "Utility Billing", "since": 2017, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Canton",        "state": "OH", "type": "muni", "bucket": "50K-100K","product": "Utility Billing", "since": 2018, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Youngstown",    "state": "OH", "type": "muni", "bucket": "50K-100K","product": "Utility Billing", "since": 2019, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Charleston",    "state": "WV", "type": "muni", "bucket": "20K-50K", "product": "Utility Billing", "since": 2016, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Huntington",    "state": "WV", "type": "muni", "bucket": "20K-50K", "product": "Utility Billing", "since": 2017, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Morgantown",    "state": "WV", "type": "muni", "bucket": "20K-50K", "product": "Utility Billing", "since": 2018, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Roanoke",       "state": "VA", "type": "muni", "bucket": "50K-100K","product": "Utility Billing", "since": 2019, "source": "Muni-Link case study", "demo": True},
    {"vendor": "Muni-Link", "muni": "Lynchburg",     "state": "VA", "type": "muni", "bucket": "50K-100K","product": "Utility Billing", "since": 2018, "source": "Muni-Link case study", "demo": True},

    # ============== TownCloud ==============
    # Cloud-native; small Southeast towns.
    {"vendor": "TownCloud", "muni": "Salem",         "state": "VA", "type": "muni", "bucket": "20K-50K", "product": "TownCloud Suite", "since": 2020, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Blacksburg",    "state": "VA", "type": "muni", "bucket": "20K-50K", "product": "TownCloud Suite", "since": 2021, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Christiansburg","state": "VA", "type": "muni", "bucket": "20K-50K", "product": "TownCloud Suite", "since": 2022, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Radford",       "state": "VA", "type": "muni", "bucket": "10K-20K", "product": "TownCloud Suite", "since": 2021, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Galax",         "state": "VA", "type": "muni", "bucket": "5K-10K",  "product": "TownCloud Suite", "since": 2022, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Boone",         "state": "NC", "type": "muni", "bucket": "10K-20K", "product": "TownCloud Suite", "since": 2021, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Hickory",       "state": "NC", "type": "muni", "bucket": "20K-50K", "product": "TownCloud Suite", "since": 2022, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Salisbury",     "state": "NC", "type": "muni", "bucket": "20K-50K", "product": "TownCloud Suite", "since": 2023, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Statesville",   "state": "NC", "type": "muni", "bucket": "20K-50K", "product": "TownCloud Suite", "since": 2022, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Aiken",         "state": "SC", "type": "muni", "bucket": "20K-50K", "product": "TownCloud Suite", "since": 2023, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Greer",         "state": "SC", "type": "muni", "bucket": "20K-50K", "product": "TownCloud Suite", "since": 2022, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Easley",        "state": "SC", "type": "muni", "bucket": "10K-20K", "product": "TownCloud Suite", "since": 2023, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Cookeville",    "state": "TN", "type": "muni", "bucket": "20K-50K", "product": "TownCloud Suite", "since": 2022, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Cleveland",     "state": "TN", "type": "muni", "bucket": "20K-50K", "product": "TownCloud Suite", "since": 2023, "source": "TownCloud case study", "demo": True},
    {"vendor": "TownCloud", "muni": "Maryville",     "state": "TN", "type": "muni", "bucket": "20K-50K", "product": "TownCloud Suite", "since": 2024, "source": "TownCloud case study", "demo": True},
]


def by_vendor():
    out = {}
    for c in CUSTOMERS:
        out.setdefault(c["vendor"], []).append(c)
    return out


def by_state(vendor=None):
    out = {}
    for c in CUSTOMERS:
        if vendor and c["vendor"] != vendor:
            continue
        out.setdefault(c["state"], []).append(c)
    return out


if __name__ == "__main__":
    bv = by_vendor()
    print(f"Total seeded customers: {len(CUSTOMERS)}")
    for v, cs in bv.items():
        print(f"  {v:22s}: {len(cs):>3}  (states: {len(set(c['state'] for c in cs))})")
