# Guess RIPE Meeting Attendee Genders

This software helps to figure out the genders of RIPE meeting
attendees. It uses the RIPE meeting web sites and genderize.io to
figure this out.

# Installation

You need Python 3 installed. Get the latest version that's convenient.

Make a Python virtual environment for this work:

    $ python3 -m venv genderenv
    $ . genderenv/bin/activate
    $ pip3 install -r requirements.txt

# Collecting Meeting Attendees

We need to get all of the attendees to the RIPE meetings:

    (genderenv) $ python3 getattendees.py
    Retrieving RIPE 1 attendees... done (0.14 seconds)... got  14 attendees
    Retrieving RIPE 2 attendees... done (0.99 seconds)... got  22 attendees
    Retrieving RIPE 3 attendees... done (0.69 seconds)... got  17 attendees
    Retrieving RIPE 4 attendees... done (0.72 seconds)... got  27 attendees
       .
       .
       .
    Retrieving RIPE 70 attendees... done (0.67 seconds)... got 678 attendees
    Retrieving RIPE 71 attendees... done (1.26 seconds)... got 525 attendees
    Retrieving RIPE 72 attendees... done (1.29 seconds)... got 672 attendees
    Retrieving RIPE 73 attendees... done (0.66 seconds)... got 254 attendees

Now we have a bunch of files of comma-separated variables (CSV files),
one for each RIPE meeting, which contains the first name and the
registration country of each attendee.

# Guessing Attendee Genders

Now that we have all of the attendees, we can try to guess the genders
of the attendees:

    (genderenv) $ python3 guessgender.py *.csv

You will end up with `ripe-genders.csv`, which has guesses about the
genders of each meeting.

Note that if you don't have an API key you will be limited to 1000
lookups per day, so you will have to spread your lookups over a 
longer period.

The software uses a local cache of name/country information to avoid
duplicate lookups in this case, which speeds up the process and
prevents unnecessary calls to the genderize.io service. This is in the
`guessgender.cache` file. If you want to flush the cache, remove the
file.

# Creating RIPE Meeting attendee database

There is also a version of the software which web-scrapes attendee
information and loads that into an SQLite database. This allows for
arbitrary SQL lookups on the attendee information, for example using
the `sqlite3` command-line tool.

First build the database:

```
$ python3 getattendees-sql.py
Retrieving RIPE 1 attendees... done (0.38 seconds)... got  14 attendees
Retrieving RIPE 2 attendees... done (0.34 seconds)... got  22 attendees
Retrieving RIPE 3 attendees... done (0.38 seconds)... got  17 attendees
  .
  .
  .
Retrieving RIPE 74 attendees... done (0.28 seconds)... got 636 attendees
Retrieving RIPE 75 attendees... done (0.29 seconds)... got 485 attendees
Retrieving RIPE 76 attendees... done (3.17 seconds)... got 771 attendees
```

Then query away:

```
$ sqlite3 ripe-attendees.db
sqlite> .schema
CREATE TABLE attendees (
            meeting_num int,
            first_name text,
            last_name text,
            country text,
            org text,
            asn int
        );
sqlite> select * from (select count(*) num_meetings, max(meeting_num) last_meeting, first_name, last_name from attendees group by lower(first_name), lower(last_name)) where num_meetings >= 50 order by num_meetings desc;
71|76|Daniel|Karrenberg
65|70|Rob|Blokzijl
62|76|Rüdiger|Volk
59|76|Wilfried|Wöber
```

As always, this is messy data that has been massaged into something
that may or may not be correct. Use with caution, but have fun!
