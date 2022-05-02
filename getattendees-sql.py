import re
import sys
import sqlite3
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

URL_MEETINGS = 'https://www.ripe.net/participate/meetings/ripe-meetings/'
url_fmt1 = URL_MEETINGS + 'ripe-%d/attendee-list'
url_fmt2 = URL_MEETINGS + 'ripe-%d/attendee-list'
url_fmt3 = URL_MEETINGS + 'ripe-%d/attendees'
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
            # remove trailing HTML
            pos = line.find('<')
            if pos != -1:
                line = line[:pos]

            country = 'XX'
            if line.endswith(" - Sweden"):
                line = line[:-len(" - Sweden")]
                country = 'SE'
            elif line.endswith(" - Italy"):
                line = line[:-len(" - Italy")]
                country = 'IT'
            elif line.endswith(" - Germany"):
                line = line[:-len(" - Germany")]
                country = 'DE'
            elif line.endswith(" - Netherlands"):
                line = line[:-len(" - Netherlands")]
                country = 'NL'
            elif line.endswith(" - France"):
                line = line[:-len(" - France")]
                country = 'FR'
            elif line.endswith(" - Switzerland"):
                line = line[:-len(" - Switzerland")]
                country = 'CH'

            # We have fixed-width columns, but the width varies by meeting.
            # One meeting separates the columns with '-', the others
            # with 2 or more spaces in between, and that seems to work okay.
            if ' - ' in line:
                info = re.split(r' - ', line)
                org_plus = re.split(r'\s\s+', info[-1])
                info[-1] = org_plus[0]
            else:
                info = re.split(r'\s\s+', line)

            info[0] = re.sub(r'\s*-\s*$', '', info[0].strip())
            names = info[0].split()

            info[1] = re.sub(r'^\s*-\s*', '', info[1].strip())
            org = info[1]
            if org.endswith(" - Sweden"):
                org = org[:-len(" - Sweden")]
                country = 'SE'
            elif org.endswith(" - Italy"):
                org = org[:-len(" - Italy")]
                country = 'IT'
            elif org.endswith(" - Germany"):
                org = org[:-len(" - Germany")]
                country = 'DE'
            elif org.endswith(" - Netherlands"):
                org = org[:-len(" - Netherlands")]
                country = 'NL'
            elif org.endswith(" - France"):
                org = org[:-len(" - France")]
                country = 'FR'
            elif org.endswith(" - Switzerland"):
                org = org[:-len(" - Switzerland")]
                country = 'CH'
            elif org.endswith("/Italy"):
                org = org[:-len("/Italy")]
                country = 'IT'
            elif org.upper().endswith("/NL"):
                org = org[:-len("/NL")]
                country = 'NL'

            fname = names[0]
            lname = ' '.join(names[1:])

            # some fix-ups
            if fname == 'R"udiger':
                fname = 'Rüdiger'
            elif fname == 'Daniel_Karrenberg':
                fname = 'Daniel'
            elif lname.endswith(" (Chairman)"):
                lname = lname[:-len(" (Chairman)")]

            attendees.append({'first_name': fname.title(),
                              'last_name': lname.title(),
                              'country': country,
                              'org': org,
                              'asn': None})

    return attendees


# Meeting 3 is basically impossible to parse, just hard code it
def parse_meeting_3(soup):
    data = (('Rob',          'Blokzjil',      'XX', 'NIKHEF/HEPnet'),
            ('Mats',         'Brunell',       'XX', 'NORDUnet'),
            ('Francis',      'Dupont',        'XX', 'INRIA/Fnet'),
            ('Yves',         'Devilles',      'XX', 'INRIA/Fnet'),
            ('Antonio',      'Blasco Bonito', 'IT', 'GARR'),
            ('Hans',         'Frese',         'XX', 'DESY'),
            ('Thomas',       'Lenggenhager',  'CH', 'SWITCH'),
            ('Niall',        "O'Reilly",      'XX', 'EARN'),
            ('Paul',         'Bryant',        'GB', 'Rutherford'),
            ('Ferdinand',    'Hommes',        'XX', 'GMD'),
            ('Arnold',       'Nipper',        'XX', 'Xlink/Karlsruhe'),
            ('Erik',         'Huizer',        'NL', 'SURFnet'),
            ('James',        'Barr',          'NL', 'NIKHEF'),
            ('Bernhard',     'Stockman',      'XX', 'NORDUnet'),
            ('Carl-Herbert', 'Rokitansky',    'XX', 'Fern Uni Hopen'),
            ('Rüdiger',      'Volk',          'XX', 'EUnet/U Dortmund'),
            ('Daniel',       'Karrenberg',    'XX', 'EUnet/Europe'),)
    attendees = []
    for datum in data:
        attendees.append({'first_name': datum[0],
                          'last_name': datum[1],
                          'country': datum[2],
                          'org': datum[3],
                          'asn': None})
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
        # remove trailing HTML
        pos = line.find('<')
        if pos != -1:
            line = line[:pos]
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

            # We have fixed-width columns, but the width varies by meeting.
            # We can split into columns with 2 or more spaces in between,
            # and that seems to work okay.
            info = re.split(r'\s\s+', line, maxsplit=1)

            # Some meetings use ':' as separator, probably for some
            # nostalgic reason to do with RIPE-81 version of the RIPE
            # Database.
            if len(info) == 1:
                info = line.split(':')

            names = info[0].strip().split()
            org = info[1].strip()

            fname = names[0]

            # some names have an underscore or a dot separating the last name
            for ch in "_.":
                if ch in fname:
                    split_fname = fname.split(ch)
                    fname = split_fname[0]
                    names = split_fname + names[1:]

            lname = ' '.join(names[1:])

            attendees.append({'first_name': fname.title(),
                              'last_name': lname.title(),
                              'country': 'XX',
                              'org': org,
                              'asn': None})

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
        lname = ' '.join(info[1:])

        # skip name line
        lines = lines[1:]
        # handle page break stuck in here
        if "- 32 -" in lines[0]:
            lines = lines[3:]
        # skip organization line
        org = lines[0].strip()
        lines = lines[1:]
        # if we have an e-mail, skip e-mail line
        if (("_at_" in lines[0]) or
                ("@" in lines[0]) or lines[0].endswith(".sk")):
            lines = lines[1:]
        attendees.append({'first_name': fname.title(),
                          'last_name': lname.title(),
                          'country': 'XX',
                          'org': org,
                          'asn': None})

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
    n = 0
    for line in lines:
        if line and (not line[0].isspace()):
            n = n + 1
            info = re.split(r'\s\s+', line, maxsplit=1)
            name = info[0].strip().split()
            if len(info) == 2:
                org = info[1]
            else:
                org = None
            fname = name[0]
            lname = ' '.join(name[1:])
            attendees.append({'first_name': fname.title(),
                              'last_name': lname.title(),
                              'country': 'XX',
                              'org': org,
                              'asn': None})

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
            info = name.split()
            fname = info[0]
            lname = ' '.join(info[1:])
            org = cols[1]
            attendees.append({'first_name': fname.title(),
                              'last_name': lname.title(),
                              'country': 'XX',
                              'org': org,
                              'asn': None})

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
            name, country, org = cols[0], cols[1].strip(), cols[2]
            info = name.split()
            fname = info[0]
            info = info[1:]
            # fix-up some broken first names
            if fname == "Dr":
                fname = info[0]
                info = info[1:]
            elif fname == "CTO":
                fname = info[1]
                info = info[1:]
            # generate a last name
            lname = ' '.join(info)
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
            if country == '':
                country = None
            attendees.append({'first_name': fname.title(),
                              'last_name': lname.title(),
                              'country': country,
                              'org': org,
                              'asn': None})

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
            lname, fname, country, org = (cols[0], cols[1], cols[2].strip(),
                                          cols[3])
            # a few strange country entries
            if country == "GERMANY":
                country = 'DE'
            elif country == "ITALY":
                country = 'IT'
            # used to use UK for GB, because Brits don't know their code
            elif country == 'UK':
                country = 'GB'
            elif country == '':
                country = None
            attendees.append({'first_name': fname,
                              'last_name': lname,
                              'country': country,
                              'org': org,
                              'asn': None})

    return attendees


# For RIPE 49 the organization & country columns were swapped, and the
# table was given an id of "t1"
def parse_table_t1(soup):
    attendees = []

    table = soup.find('table')
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        if cols:
            if len(cols) >= 4:
                lname, fname, org, country = (cols[0], cols[1],
                                              cols[2], cols[3].strip())
            else:
                lname, fname, org, country = cols[0], cols[1], cols[2], ''
            # RIPE 49 used __ for some attendees
            if country == '__':
                country = ''
            # used to use UK for GB, because Brits don't know their code
            if country == "UK":
                country = 'GB'
            elif country == '':
                country = None
            attendees.append({'first_name': fname,
                              'last_name': lname,
                              'country': country,
                              'org': org,
                              'asn': None})

    return attendees


# RIPE 59 changed the name of the table (and the URL)
def parse_table_attendee(soup):
    attendees = []

    table = soup.find('table', attrs={'id': 'attendeeTable'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        lname, fname, org, country = cols[0], cols[1], cols[2], cols[3].strip()
        if country.strip() == '':
            country = None
        attendees.append({'first_name': fname,
                          'last_name': lname,
                          'country': country,
                          'org': org,
                          'asn': None})

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
    if "Global" in fixed:
        fixed = ''
    if fixed.strip() == '':
        fixed = None
    return fixed


# RIPE 64 switched to putting first name first
def parse_fname_lname(soup):
    attendees = []

    table = soup.find('table', attrs={'id': 'attendeeTable'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        fname, lname, org, country, = (cols[0], cols[1], cols[2],
                                       country_fixups(cols[3]))
        if len(cols) == 6:
            asn = cols[5]
        else:
            asn = None
        attendees.append({'first_name': fname,
                          'last_name': lname,
                          'country': country,
                          'org': org,
                          'asn': asn})

    return attendees


# RIPE 74 added an empty first column
def parse_empty_fname_lname(soup):
    attendees = []

    table = soup.find('table', attrs={'id': 'attendeeTable'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        cols = [col.text for col in row.find_all('td')]
        fname, lname, org, country, asn = (cols[1], cols[2], cols[3],
                                           country_fixups(cols[4]), cols[6])
        attendees.append({'first_name': fname,
                          'last_name': lname,
                          'country': country,
                          'org': org,
                          'asn': asn})
    return attendees


mtg_def = [
    (  1, url_fmt1, parse_table ),
    (  2, url_fmt1, parse_table ),
    (  3, url_fmt1, parse_table ),
    (  4, url_fmt1, parse_table ),
    (  5, url_fmt1, parse_table ),
    (  6, url_fmt1, parse_table ),
    (  7, url_fmt1, parse_table ),
    (  8, url_fmt1, parse_table ),
    (  9, url_fmt1, parse_table ),
    ( 10, url_fmt1, parse_table ),
    ( 11, url_fmt1, parse_table ),
    ( 12, url_fmt1, parse_table ),
    ( 13, url_fmt1, parse_table ),
    ( 14, url_fmt1, parse_table ),
    ( 15, url_fmt1, parse_table ),
    ( 16, url_fmt1, parse_table ),
    ( 17, url_fmt1, parse_table ),
    ( 18, url_fmt1, parse_table ),
    ( 19, url_fmt1, parse_table ),
    ( 20, url_fmt1, parse_table ),
    ( 21, url_fmt1, parse_table ),
    ( 22, url_fmt1, parse_table ),
    ( 23, url_fmt1, parse_table ),
    ( 24, url_fmt1, parse_table ),
    ( 25, url_fmt1, parse_table ),
    ( 26, url_fmt1, parse_table ),
    # 27 is missing from the RIPE web site
    ( 28, url_fmt1, parse_table ),
    ( 29, url_fmt1, parse_cc ),
    ( 30, url_fmt1, parse_cc ),
    ( 31, url_fmt1, parse_cc ),
    ( 32, url_fmt1, parse_cc ),
    ( 33, url_fmt1, parse_cc ),
    ( 34, url_fmt1, parse_cc ),
    ( 35, url_fmt1, parse_cc ),
    ( 36, url_fmt1, parse_cc ),
    ( 37, url_fmt1, parse_cc ),
    ( 38, url_fmt1, parse_cc ),
    ( 39, url_fmt1, parse_cc ),
    ( 40, url_fmt1, parse_cc ),
    ( 41, url_fmt1, parse_cc ),
    ( 42, url_fmt1, parse_cc ),
    ( 43, url_fmt1, parse_cc ),
    ( 44, url_fmt1, parse_lname_fname),
    ( 45, url_fmt1, parse_lname_fname),
    ( 46, url_fmt1, parse_lname_fname),
    ( 47, url_fmt1, parse_lname_fname),
    ( 48, url_fmt1, parse_lname_fname),
    ( 49, url_fmt1, parse_table_t1 ),
    ( 50, url_fmt1, parse_table_t1 ),
    ( 51, url_fmt1, parse_table_t1 ),
    ( 52, url_fmt1, parse_table_t1 ),
    ( 53, url_fmt1, parse_table_t1 ),
    ( 54, url_fmt1, parse_table_t1 ),
    ( 55, url_fmt1, parse_table_t1 ),
    ( 56, url_fmt1, parse_table_t1 ),
    ( 57, url_fmt1, parse_table_t1 ),
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
    ( 78, url_fmt8, parse_empty_fname_lname ),
    ( 79, url_fmt8, parse_empty_fname_lname ),
]


def init_db():
    db = sqlite3.connect('ripe-attendees.db')
    c = db.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendees (
            meeting_num int,
            first_name text,
            last_name text,
            country text,
            org text,
            asn int
        )
    ''')
    c.close()
    return db


def reset_meeting(db, meeting_num):
    c = db.cursor()
    c.execute('''
       DELETE FROM attendees WHERE meeting_num=?
    ''', (meeting_num,))
    c.close()


def final_fixups(attendees):
    for attendee in attendees:
        attendee['last_name'] = attendee['last_name'].title()
        attendee['first_name'] = attendee['first_name'].title()
        if attendee['last_name'] == 'Volk':
            if attendee['first_name'] == 'Ruediger':
                attendee['first_name'] = 'Rüdiger'
            elif attendee['first_name'] == 'Rudiger':
                attendee['first_name'] = 'Rüdiger'
        elif attendee['first_name'] == 'Wilfried':
            if attendee['last_name'] == 'Woeber':
                attendee['last_name'] = 'Wöber'
            elif attendee['first_name'] == 'Rudiger':
                attendee['first_name'] = 'Rüdiger'
        elif attendee['first_name'] == 'Mirjam':
            if attendee['last_name'] == 'Kuehne':
                attendee['last_name'] = 'Kühne'
            if attendee['last_name'] == 'Kuhne':
                attendee['last_name'] = 'Kühne'


def write_attendee(db, meeting_num, attendee):
    c = db.cursor()
    c.execute('''
        INSERT INTO attendees (meeting_num,
                               first_name, last_name, country, org, asn)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (meeting_num,
          attendee['first_name'],
          attendee['last_name'],
          attendee['country'],
          attendee['org'],
          attendee['asn']))
    c.close()


def main():
    db = init_db()
    for (mtg, url_fmt, scraper) in mtg_def:
        url = url_fmt % mtg
        sys.stdout.write('Retrieving RIPE %2d attendees...' % mtg)
        sys.stdout.flush()
        time_a = time.monotonic()
        page = requests.get(url)
        time_b = time.monotonic()
        sys.stdout.write(" done (%.2f seconds)..." % (time_b - time_a))
        soup = BeautifulSoup(page.content, 'lxml')
        attendees = scraper(soup)
        final_fixups(attendees)
        sys.stdout.write(" got %3d attendees\n" % len(attendees))
        reset_meeting(db, mtg)
        for attendee in attendees:
            write_attendee(db, mtg, attendee)
        db.commit()


if __name__ == '__main__':
    main()
