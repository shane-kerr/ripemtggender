import csv
import re
import sys

from genderize import Genderize

# if you want to do a lot of queries you can put your API key here
API_KEY = None

if API_KEY:
    genderize = Genderize(api_key=API_KEY)
else:
    genderize = Genderize()

# TODO: figure out what to do with names like 'H.' or 'A'

# Note some are wrong (like "Miek")

for file_name in sys.argv[1:]:
    mtg_id = file_name[4:6]
    print("--- RIPE %s ----------------" % mtg_id)

    first_names_by_country = {}
    with open(file_name, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for first_name, country in reader:
            tmp = first_names_by_country.get(country, [])
            tmp.append(first_name)
            first_names_by_country[country] = tmp

    xy_sum = 0.0
    xx_sum = 0.0
    na_sum = 0.0
    for country, names in first_names_by_country.items():
        print("== Country '%s' ==" % country)
        unknown_gender = []
        # we have to split our names up into sets of no bigger than 10,
        # because that is all the API supports
        while names:
            query_names = names[0:10]
            names = names[10:]
            if country in ('XX', ''):
                probabilities = genderize.get(query_names)
            else:
                probabilities = genderize.get(query_names, country_id=country)
            for gender_info in probabilities:
                if gender_info['gender'] in ('male', 'female'):
                    if gender_info['gender'] == 'male':
                        manliness = gender_info['probability']
                    else:
                        manliness = 1.0 - gender_info['probability']
                    xy_sum += manliness
                    xx_sum += 1.0 - manliness
                    if manliness > 0.5:
                        symbol = '♂'
                    else:
                        symbol = '♀'
                    name = gender_info['name']
                    print("%.2f  %s %s" % (manliness, symbol, name))
                else:
                    unknown_gender.append(gender_info['name'])

        # don't re-try unknown gender if we have an unknown country already
        if country in ('XX', ''):
            continue

        while unknown_gender:
            query_names = unknown_gender[0:10]
            unknown_gender = unknown_gender[10:]
            probabilities = genderize.get(query_names)
            for gender_info in probabilities:
                if gender_info['gender'] in ('male', 'female'):
                    if gender_info['gender'] == 'male':
                        manliness = gender_info['probability']
                    else:
                        manliness = 1.0 - gender_info['probability']
                    xy_sum += manliness
                    xx_sum += 1.0 - manliness
                    if manliness > 0.5:
                        symbol = '♂'
                    else:
                        symbol = '♀'
                    name = gender_info['name']
                    print("%.2f  %s %s (without country)" % 
                          (manliness, symbol, name))
                else:
                    na_sum += 1.0
                    print("-.--  ? %s" % (gender_info['name']))

    with open('ripe-genders.csv', 'a', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow((mtg_id, "%.2f" % xy_sum,
                                 "%.2f" % xx_sum,
                                 "%.2f" % na_sum))
