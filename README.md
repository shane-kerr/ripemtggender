# Guess RIPE Meeting Attendee Genders

This software helps to figure out the genders of RIPE meeting
attendees. It uses the RIPE meeting web sites and genderize.io to
figure this out.

# Installation

You need Python 3 installed. Get the latest version that's convenient.

Make a Python virtual environment for this work:

    $ python3 -m venv genderenv
    $ . genderenv/bin/activate
    (genderenv) $ pip3 install beautifulsoup4
    (genderenv) $ pip3 install requests
    (genderenv) $ pip3 install lxml
    (genderenv) $ pip3 install Genderize

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
longer period. It will make sense to use a local cache of name/country
information to avoid duplicate lookups in this case - actually that
would always help.
