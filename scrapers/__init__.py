"""Medical job scrapers for Australian portals."""

from scrapers.aggregators import AGGREGATOR_SCRAPERS
from scrapers.govt_portals import GOVT_SCRAPERS
from scrapers.hospital_careers import HOSPITAL_SCRAPERS
from scrapers.specialty_boards import SPECIALTY_SCRAPERS
from scrapers.workday_scraper import scrape_mercy_workday

ALL_SCRAPERS = {
    **GOVT_SCRAPERS,
    **HOSPITAL_SCRAPERS,
    **SPECIALTY_SCRAPERS,
    **AGGREGATOR_SCRAPERS,
    "mercy_workday": scrape_mercy_workday,
}
