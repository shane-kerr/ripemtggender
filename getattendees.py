import csv
import re
import sys
import time

# RIPE 27 doesn't seem to have an attendee list
# RIPE 35 and RIPE 37 have the SAME attendee list (!)
# Did RIPE 36 really only have 58 attendees? RIPE 38 only 120?

from bs4 import BeautifulSoup
import requests

# Note: Once we start recording first name we have problems with
#       people from cultures with multiple given names, or other
#       ways of naming, like "Hans Petter" or "Juan Manuel".

# XXX RIPE 58 Matja<U+009E>,SI

url_fmt1 = 'https://www.ripe.net/participate/meetings/ripe-meetings/ripe-%d/attendee-list'
url_fmt2 = 'https://www.ripe.net/participate/meetings/ripe-meetings/ripe-%d/attendee-list'
url_fmt3 = 'https://www.ripe.net/participate/meetings/ripe-meetings/ripe-%d/attendees'
url_fmt4 = 'http://ripe%d.ripe.net/attendee_list.html'
url_fmt5 = 'http://ripe%d.ripe.net/attendees.html'
url_fmt6 = 'https://ripe%d.ripe.net/registration/attendee-list/'
url_fmt7 = 'https://ripe%d.ripe.net/attendee-list/'
url_fmt8 = 'https://ripe%d.ripe.net/attend/attendee-list/'

# Our earliest attendee lists are just HTML text
def parse_early(soup):
    text = None
    for div in soup.find_all('div'):
        div_id = div.get('id')
        if div_id and (div_id == 'content-core'):
            text = str(div)

    attendees = []
    lines = text.split("<br/>")
    if not lines:
        lines = text.split("<br />")
    for line in lines:
        line = re.sub(r'\n', ' ', line)
        line = re.sub(r'.*<p>', '', line)
        line = re.sub(r'</p>.*', '', line)
        line = line.strip()
        if line:
            fname = line.split()[0]
            # some fix-ups
            if fname == 'R"udiger':
                fname = 'Rüdiger'
            elif fname == 'Daniel_Karrenberg':
                fname = 'Daniel'
            attendees.append((fname, 'XX'))

    return attendees


# A bit later, early meetings use pre-formatted text
def parse_pre(soup):
    text = None
    for div in soup.find_all('div'):
        div_id = div.get('id')
        if div_id and (div_id == 'content-core'):
            text = str(div.pre)[5:-6]

    attendees = []
    lines = text.split("<br/>")
    if not lines:
        lines = text.split("<br />")
    for line in lines:
        line = line.strip()
        if line:
            # filter out "PARTICIPANTS" line if present
            if line.startswith("PARTICIPANTS"):
                continue
            # meeting 14 left some nroff formatting in
            if line.startswith(".TE"):
                continue
            # filter out some crap from meeting 22
            if line[0] == '_':
                continue
            if line.startswith('ripe-'):
                continue
            if line.startswith('Minutes'):
                continue
            fname = line.split()[0]
            # some names have an underscore or a dot separating the last name
            fname = fname.split('_')[0]
            fname = fname.split('.')[0]
            attendees.append((fname, 'XX'))

    return attendees

# Meeting 19 has 3 lines per attendee: name, company, e-mail
def parse_three_lines(soup):
    attendees = []

    text = None
    for div in soup.find_all('div'):
        div_id = div.get('id')
        if div_id and (div_id == 'content-core'):
            text = str(div.pre)[5:-6]

    lines = text.split("<br/>")
    if not lines:
        lines = text.split("<br />")
    while lines:
        if not lines[0].strip(): 
            break

        info = lines[0].split()
        fname = info[0]
        if fname == "Dr":
            fname = info[1]

        # skip name line
        lines = lines[1:]
        # handle page break stuck in here
        if "- 32 -" in lines[0]:
            lines = lines[3:]
        # skip organization line
        lines = lines[1:]
        # if we have an e-mail, skip e-mail line
        if ("_at_" in lines[0]) or ("@" in lines[0]) or lines[0].endswith(".sk"):
            lines = lines[1:]
        attendees.append((fname, 'XX'))

    return attendees

# RIPE 20, 25, and 26 have 2-lines per attendee, we only want the first line
def parse_two_lines(soup):
    attendees = []

    text = None
    for div in soup.find_all('div'):
        div_id = div.get('id')
        if div_id and (div_id == 'content-core'):
            text = str(div.pre)[5:-6]

    lines = text.split("<br/>")
    if not lines:
        lines = text.split("<br />")
    for line in lines:
        if line and (not line[0].isspace()):
            fname = line.split()[0]
            attendees.append((fname, 'XX'))

    return attendees

# RIPE 28 started providing attendee list in an HTML table
def parse_table(soup):
    attendees = []

    table = soup.find('table')
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        if cols and cols[0]:
            name = cols[0]
            fname = name.split()[0]
            attendees.append((fname, 'XX'))

    return attendees

# For RIPE 29 a country code was added to the HTML table
def parse_cc(soup):
    attendees = []

    table = soup.find('table')
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        # handle RIPE 40 newly-broken table
        if cols and cols[0] == '\xa0':
            continue
        # handle most cases
        if cols and cols[0]:
            name, country = cols[0], cols[1].strip()
            info = name.split()
            fname = info[0]
            # fix-up some broken first names
            if fname == "Dr":
                fname = info[1]
            if fname == "CTO":
                fname = info[1]
            # somehow this made it in... the name seems to be an Israeli name
            if country == '972':
                country = 'IL'
            # in RIPE 33 and RIPE 34 "USA" was used as a country code
            if country == "USA":
                country = 'US'
            # used to use UK for GB, because Brits don't know their code
            if country == "UK":
                country = 'GB'
            # RIPE 33 has a bogus country, 'D'
            # RIPE 34 has more bogus countries, like '1', 'B'
            if len(country) != 2:
                country = ''
            # at some point, e-mail got added as the country code
            if ("@" in country) or (" _at_ " in country):
                country = ''
            attendees.append((fname, country))

    return attendees

# Starting at RIPE 44 first and last names were recorded separately
def parse_lname_fname(soup):
    attendees = []

    table = soup.find('table')
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        if cols:
            lname, fname, country = cols[0], cols[1], cols[2].strip()
            # a few strange country entries
            if country == "GERMANY":
                country = 'DE'
            elif country == "ITALY":
                country = 'IT'
            # used to use UK for GB, because Brits don't know their code
            elif country == 'UK':
                country = 'GB'
            attendees.append((fname, country))

    return attendees

# For RIPE 49 the organization & country columns were swapped, and the 
# table was given an id of "t1"
def parse_table_t1(soup):
    attendees = []

    table = soup.find('table', attrs={'id': 't1'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        if cols:
            if len(cols) >= 4: 
                lname, fname, country = cols[0], cols[1], cols[3].strip()
            else:
                lname, fname, country = cols[0], cols[1], ''
            # RIPE 49 used __ for some attendees
            if country == '__':
                country = ''
            # used to use UK for GB, because Brits don't know their code
            if country == "UK":
                country = 'GB'
            attendees.append((fname, country))

    return attendees

# RIPE 59 changed the name of the table (and the URL)
def parse_table_attendee(soup):
    attendees = []

    table = soup.find('table', attrs={'id': 'attendeeTable'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        lname, fname, country = cols[0], cols[1], cols[3].strip()
        attendees.append((fname, country))

    return attendees

# Some country fixups
def country_fixups(country):
    fixed = country.strip()
    if fixed == 'Palestinian Territory':
        fixed = 'PS'
    if fixed == 'Moldova':
        fixed = 'MD'
    if fixed == 'Macedonia':
        fixed = 'MK'
    # Bravehearts
    if fixed == 'Scotland':
        fixed = 'GB'
    if "Taiwan" in fixed:
        fixed = 'TW'
    if "Stateless" in fixed:
        fixed = ''
    return fixed

# RIPE 64 switched to putting first name first
def parse_fname_lname(soup):
    attendees = []

    table = soup.find('table', attrs={'id': 'attendeeTable'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        fname, lname, country = cols[0], cols[1], country_fixups(cols[3])
        attendees.append((fname, country))

    return attendees

# RIPE 74 added an empty first column
def parse_empty_fname_lname(soup):
    attendees = []

    table = soup.find('table', attrs={'id': 'attendeeTable'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        fname, lname, country = cols[1], cols[2], country_fixups(cols[4])
        attendees.append((fname, country))

    return attendees

mtg_def = [
    (  1, url_fmt1, parse_early ),
    (  2, url_fmt1, parse_early ),
    (  3, url_fmt1, parse_early ),
    (  4, url_fmt1, parse_early ),
    (  5, url_fmt1, parse_early ),
    (  6, url_fmt1, parse_early ),
    (  7, url_fmt1, parse_early ),
    (  8, url_fmt1, parse_early ),
    (  9, url_fmt2, parse_pre ),
    ( 10, url_fmt2, parse_pre ),
    ( 11, url_fmt2, parse_pre ),
    ( 12, url_fmt2, parse_pre ),
    ( 13, url_fmt2, parse_pre ),
    ( 14, url_fmt2, parse_pre ),
    ( 15, url_fmt2, parse_pre ),
    ( 16, url_fmt3, parse_pre ),
    ( 17, url_fmt2, parse_pre ),
    ( 18, url_fmt2, parse_pre ),
    ( 19, url_fmt2, parse_three_lines ),
    ( 20, url_fmt2, parse_two_lines ),
    ( 21, url_fmt2, parse_pre ),
    ( 22, url_fmt2, parse_pre ),
    ( 23, url_fmt2, parse_pre ),
    ( 24, url_fmt1, parse_early ),
    ( 25, url_fmt2, parse_two_lines ),
    ( 26, url_fmt2, parse_two_lines ),
    # 27 is missing from the RIPE web site
    ( 28, url_fmt2, parse_table ),
    ( 29, url_fmt2, parse_cc ),
    ( 30, url_fmt2, parse_cc ),
    ( 31, url_fmt2, parse_cc ),
    ( 32, url_fmt2, parse_cc ),
    ( 33, url_fmt2, parse_cc ),
    ( 34, url_fmt2, parse_cc ),
    ( 35, url_fmt2, parse_cc ),
    ( 36, url_fmt2, parse_cc ),
    ( 37, url_fmt2, parse_cc ),
    ( 38, url_fmt2, parse_cc ),
    ( 39, url_fmt2, parse_cc ),
    ( 40, url_fmt2, parse_cc ),
    ( 41, url_fmt2, parse_cc ),
    ( 42, url_fmt2, parse_cc ),
    ( 43, url_fmt2, parse_cc ),
    ( 44, url_fmt2, parse_lname_fname ),
    ( 45, url_fmt2, parse_lname_fname ),
    ( 46, url_fmt2, parse_lname_fname ),
    ( 47, url_fmt2, parse_lname_fname ),
    ( 48, url_fmt2, parse_lname_fname ),
    ( 49, url_fmt2, parse_table_t1 ),
    ( 50, url_fmt2, parse_table_t1 ),
    ( 51, url_fmt2, parse_table_t1 ),
    ( 52, url_fmt2, parse_table_t1 ),
    ( 53, url_fmt2, parse_table_t1 ),
    ( 54, url_fmt2, parse_table_t1 ),
    ( 55, url_fmt2, parse_table_t1 ),
    ( 56, url_fmt2, parse_table_t1 ),
    ( 57, url_fmt2, parse_table_t1 ),
    ( 58, url_fmt4, parse_table_t1 ),
    ( 59, url_fmt5, parse_table_attendee ),
    ( 60, url_fmt5, parse_table_attendee ),
    ( 61, url_fmt6, parse_table_attendee ),
    ( 62, url_fmt7, parse_table_attendee ),
    ( 63, url_fmt7, parse_table_attendee ),
    ( 64, url_fmt7, parse_fname_lname ),
    ( 65, url_fmt7, parse_fname_lname ),
    ( 66, url_fmt8, parse_fname_lname ),
    ( 67, url_fmt8, parse_fname_lname ),
    ( 68, url_fmt8, parse_fname_lname ),
    ( 69, url_fmt8, parse_fname_lname ),
    ( 70, url_fmt8, parse_fname_lname ),
    ( 71, url_fmt8, parse_fname_lname ),
    ( 72, url_fmt8, parse_fname_lname ),
    ( 73, url_fmt8, parse_fname_lname ),
    ( 74, url_fmt8, parse_empty_fname_lname ),
    ( 75, url_fmt8, parse_empty_fname_lname ),
    ( 76, url_fmt8, parse_empty_fname_lname ),
    ( 77, url_fmt8, parse_empty_fname_lname ),
]

for (mtg, url_fmt, scraper) in mtg_def:
    url = url_fmt % mtg
    sys.stdout.write('Retrieving RIPE %d attendees...' % mtg)
    sys.stdout.flush()
    time_a = time.monotonic()
    page = requests.get(url)
    time_b = time.monotonic()
    sys.stdout.write(" done (%.2f seconds)..." % (time_b - time_a))
    soup = BeautifulSoup(page.content, 'lxml')
    attendees = scraper(soup)
    with open('ripe%02d-attendees.csv' % mtg, 'w', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for attendee in attendees:
            writer.writerow(attendee)
    sys.stdout.write(" got %3d attendees\n" % len(attendees))
