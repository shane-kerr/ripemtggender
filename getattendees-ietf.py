import csv
import re
import sys
import time

from bs4 import BeautifulSoup
import requests

url_fmt_ietf = 'https://www.ietf.org/registration/ietf%d/attendance.py'

def parse_ietf1(soup):
    attendees = []

    # Yes, this is brittle. We are scraping, it will be brittle.
    all_tables = soup.findAll("table")
    table_body = all_tables[2]

    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        if cols:
            lname, fname, country, on_site = cols[0], cols[1], cols[3], cols[4]
            if on_site == "Yes":
                attendees.append((fname, country))

    return attendees

def parse_ietf2(soup):
    attendees = []

    # Yes, this is brittle. We are scraping, it will be brittle.
    all_tables = soup.findAll("table")
    table_body = all_tables[1]

    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        if cols:
            lname, fname, country, on_site = cols[1], cols[2], cols[4], cols[5]
            if on_site == "Yes":
                attendees.append((fname, country))

    return attendees

mtg_def = [
    ( 87, url_fmt_ietf, parse_ietf1 ),
    ( 88, url_fmt_ietf, parse_ietf1 ),
    ( 89, url_fmt_ietf, parse_ietf1 ),
    ( 90, url_fmt_ietf, parse_ietf1 ),
    ( 91, url_fmt_ietf, parse_ietf1 ),
    ( 92, url_fmt_ietf, parse_ietf1 ),
    ( 93, url_fmt_ietf, parse_ietf2 ),
    ( 94, url_fmt_ietf, parse_ietf2 ),
    ( 95, url_fmt_ietf, parse_ietf2 ),
    ( 96, url_fmt_ietf, parse_ietf2 ),
    ( 97, url_fmt_ietf, parse_ietf2 ),
    ( 98, url_fmt_ietf, parse_ietf2 ),
    ( 99, url_fmt_ietf, parse_ietf2 ),
]

for (mtg, url_fmt, scraper) in mtg_def:
    url = url_fmt % mtg
    sys.stdout.write('Retrieving IETF %d attendees...' % mtg)
    sys.stdout.flush()
    time_a = time.monotonic()
    page = requests.get(url)
    time_b = time.monotonic()
    sys.stdout.write(" done (%.2f seconds)..." % (time_b - time_a))
    soup = BeautifulSoup(page.content, 'lxml')
    attendees = scraper(soup)
    with open('ietf%03d-attendees.csv' % mtg, 'w', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for attendee in attendees:
            writer.writerow(attendee)
    sys.stdout.write(" got %3d attendees\n" % len(attendees))
