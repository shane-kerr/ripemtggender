import csv
import pickle
import re
import sys
import time

from genderize import Genderize, GenderizeException

# if you want to do a lot of queries you can put your API key here
#API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
API_KEY = None

if API_KEY:
    genderize = Genderize(api_key=API_KEY)
else:
    genderize = Genderize()

class gender_cache:
    """
    This is a class which you can look up names in genderize.io, which
    remembers calls and caches the answers to avoid repeated lookups.
    This removes something like 2/3 or 3/4 of calls, making it faster
    and also avoiding running up your query limits.
    """
    def __init__(self, file_name):
        try:
            with open(file_name, 'rb') as f:
                self.cache = pickle.load(f)
        except IOError:
            self.cache = {}
        self.file_name = file_name
        self.hits = 0
        self.misses = 0

    def save(self):
        with open(self.file_name, 'wb') as f:
            pickle.dump(self.cache, f)

    def add(self, name, gender, probability, country=None):
        """
        Allow us to add specific names where we know the gender.
        """
        if country not in self.cache:
            self.cache[country] = {}
        self.cache[country][name] = {'name': name,
                                     'gender': gender,
                                     'probability': probability}

    # TODO: change API so that we always send 10 names per call
    def get(self, names, country_id=None):
        probabilities = []
        if country_id not in self.cache:
            self.cache[country_id] = {}
        uncached_names = []
        for name in names:
            # special-case 1-character names, either with our without
            # an dot afterwards
            if re.match(r'.[.]?$', name):
                probabilities.append({'name': name, 'gender': 'unknown'})
            # if we are in the cache just use that value
            elif name in self.cache[country_id]:
                probabilities.append(self.cache[country_id][name])
                self.hits = self.hits + 1
            # otherwise we have to look up the value
            else:
                uncached_names.append(name)
                self.misses = self.misses + 1

        if uncached_names:
            genderize_probabilities = None
            attempts = 0
            while genderize_probabilities is None:
                attempts += 1
                try:
                    if country_id is None:
                        genderize_probabilities = genderize.get(uncached_names)
                    else:
                        cid = country_id
                        genderize_probabilities = genderize.get(uncached_names,
                                                                country_id=cid)
                except GenderizeException:
                    # if we have too many attempts, then exit
                    if attempts >= 3:
                        raise
                    # otherwise delay a bit and try again
                    print("ERROR getting info, retrying")
                    time.sleep(0.1)

            for gender_info in genderize_probabilities:
                name = gender_info['name']
                self.cache[country_id][name] = gender_info
            probabilities.extend(genderize_probabilities)

        return probabilities

# Note some guesses from genderize.io are wrong (like "Miek")

# create our cache
gc = gender_cache('guessgender.cache')

# add names that we know about to our cache
gc.add(name='Rudiger', gender='male', probability=1.0)
gc.add(name='Havard', gender='male', probability=1.0)
gc.add(name='Avgust', gender='male', probability=1.0)
gc.add(name='Gerbrand', gender='male', probability=1.0)
gc.add(name='Herluf', gender='male', probability=1.0)
gc.add(name='Pedr', gender='male', probability=1.0)
gc.add(name='Wiel', gender='male', probability=1.0)
# typo of Francis?
gc.add(name='Franics', gender='male', probability=1.0)
gc.add(name='Vaclav', gender='male', probability=1.0)
gc.add(name='Nevenko', gender='male', probability=1.0)
gc.add(name='Burkard', gender='male', probability=1.0)
gc.add(name='Erzsebet', gender='female', probability=1.0)
gc.add(name='Maldwyn', gender='male', probability=1.0)
gc.add(name='Talhat', gender='male', probability=1.0)
gc.add(name='Albertas', gender='male', probability=1.0)
gc.add(name='Denesh', gender='male', probability=1.0, country='GB')
gc.add(name='Denesh', gender='male', probability=1.0, country='EU')
gc.add(name='Denesh', gender='male', probability=1.0, country='PT')
gc.add(name='Danesh', gender='male', probability=1.0, country='GB')
gc.add(name='Vittore', gender='male', probability=1.0, country='IT')
gc.add(name='Fearghas', gender='male', probability=1.0)
gc.add(name='Sico', gender='male', probability=1.0, country='NL')
gc.add(name='Christophe', gender='male', probability=1.0, country='FR')
gc.add(name='Crevan', gender='male', probability=1.0, country='IE')
gc.add(name='Fabrina', gender='female', probability=1.0)
gc.add(name='Ludger', gender='male', probability=1.0, country='DE')
gc.add(name='Giza', gender='female', probability=1.0, country='HU')
# localization issue with Björn?
gc.add(name='Bjxrn', gender='male', probability=1.0, country='NO')
gc.add(name='Godfried', gender='male', probability=1.0)
gc.add(name='Torbjorn', gender='male', probability=1.0)
gc.add(name='Abdussamad', gender='male', probability=1.0)
gc.add(name='Kuniaki', gender='male', probability=1.0, country='JP')
gc.add(name='Olafur', gender='male', probability=1.0)
gc.add(name='Iouri', gender='male', probability=1.0, country='RU')
gc.add(name='Makin', gender='male', probability=1.0)
gc.add(name='Iratxze', gender='female', probability=1.0)
gc.add(name='Ariën', gender='male', probability=1.0, country='NL')
gc.add(name='Fransico', gender='male', probability=1.0)
gc.add(name='Dhan.', gender='male', probability=1.0)
# Typo of Dominic
gc.add(name='Domimic', gender='male', probability=1.0, country='EU')
gc.add(name='Karst', gender='male', probability=1.0, country='NL')
gc.add(name='Andrzey', gender='male', probability=1.0, country='PL')
gc.add(name='Dhanpati', gender='male', probability=1.0, country='NP')
gc.add(name='Otmar', gender='male', probability=1.0)
gc.add(name='Faig', gender='male', probability=1.0, country='AZ')
gc.add(name='Kondrad', gender='male', probability=1.0, country='PL')
gc.add(name='Harmut', gender='male', probability=1.0, country='BR')
gc.add(name='Chytil', gender='male', probability=1.0)
gc.add(name='Zbynek', gender='male', probability=1.0, country='CZ')
gc.add(name='Regnar', gender='male', probability=1.0, country='DK')
gc.add(name='Sampsamatti', gender='male', probability=1.0, country='FI')
gc.add(name='Moyaze', gender='male', probability=1.0, country='GB')
gc.add(name='Iljitsch', gender='male', probability=1.0, country='NL')
gc.add(name='Iván', gender='male', probability=1.0)
gc.add(name='Håkan', gender='male', probability=1.0, country='SE')
# localization issue with Håkan?
gc.add(name='HÃ¥kan', gender='male', probability=1.0, country='SE')
gc.add(name='Andew', gender='male', probability=1.0)
gc.add(name='Taiji', gender='male', probability=1.0)
gc.add(name='Alipasha', gender='male', probability=1.0, country='IR')
gc.add(name='Huug', gender='male', probability=1.0, country='NL')
gc.add(name='Taiji', gender='male', probability=1.0, country='JP')
gc.add(name='Abdelnaser', gender='male', probability=1.0)
gc.add(name='Abdelnasir', gender='male', probability=1.0)
gc.add(name='Spiridon', gender='male', probability=1.0, country='GR')
gc.add(name='Shaviv', gender='male', probability=1.0, country='IL')
gc.add(name='Enifeni', gender='female', probability=1.0, country='NG')
gc.add(name='Sidhom', gender='male', probability=1.0, country='TN')
gc.add(name='Stjepko', gender='male', probability=1.0, country='HR')
gc.add(name='Jelte', gender='male', probability=1.0, country='NL')
gc.add(name='Rowald', gender='male', probability=1.0, country='NL')
gc.add(name='Irmhild', gender='female', probability=1.0, country='DE')
gc.add(name='Aliaksei', gender='male', probability=1.0, country='BY')
gc.add(name='Heidrich', gender='male', probability=1.0, country='HU')
gc.add(name='Potapov', gender='male', probability=1.0, country='RU')
gc.add(name='Potapova', gender='female', probability=1.0, country='RU')
gc.add(name='Tereze', gender='female', probability=1.0, country='CZ')
gc.add(name='Donetella', gender='female', probability=1.0, country='IT')
gc.add(name='Rafaël', gender='male', probability=1.0, country='NL')
gc.add(name='Macek', gender='male', probability=1.0, country='CZ')
gc.add(name='Neana', gender='female', probability=1.0)
gc.add(name='Kursad', gender='male', probability=1.0, country='TR')
gc.add(name='Turkeer', gender='male', probability=1.0, country='TR')
gc.add(name='Katsuyasu', gender='male', probability=1.0)
gc.add(name='Ischa', gender='female', probability=1.0)
gc.add(name='Andranik', gender='male', probability=1.0, country='AM')
gc.add(name='Isacco', gender='male', probability=1.0)
gc.add(name='Leanca', gender='female', probability=1.0, country='RO')
gc.add(name='Edik', gender='male', probability=1.0, country='UA')
gc.add(name='Zakar', gender='male', probability=1.0, country='AM')
gc.add(name='Hagen', gender='male', probability=1.0, country='DE')
gc.add(name='Thorleif', gender='male', probability=1.0, country='DE')
gc.add(name='Mahamuda', gender='female', probability=1.0, country='GI')
gc.add(name='Yoshiro', gender='male', probability=1.0)
gc.add(name='Stefphen', gender='male', probability=1.0, country='NL')
gc.add(name='Eugénio', gender='male', probability=1.0, country='PT')
gc.add(name='Moushegh', gender='male', probability=1.0, country='AM')
gc.add(name='Timme', gender='male', probability=1.0)
gc.add(name='Ryoichi', gender='male', probability=1.0)
gc.add(name='Gheorghita', gender='female', probability=1.0, country='RO')
gc.add(name='Jugoslav', gender='male', probability=1.0, country='SI')
gc.add(name='Ljupche', gender='male', probability=1.0)
gc.add(name='Reinart', gender='male', probability=1.0, country='NL')
gc.add(name='Vladyslav', gender='male', probability=1.0, country='UA')
gc.add(name='Ebben', gender='male', probability=1.0, country='US')
gc.add(name='Ndricim', gender='male', probability=1.0, country='AL')
gc.add(name='Artavazd', gender='male', probability=1.0)
gc.add(name='Toshikatsu', gender='male', probability=1.0)
gc.add(name='Stancu', gender='male', probability=1.0, country='RO')
gc.add(name='Salhida', gender='female', probability=1.0)
gc.add(name='Michl', gender='male', probability=1.0, country='CZ')
gc.add(name='Sváťa', gender='male', probability=1.0, country='CZ')
gc.add(name='Pall', gender='male', probability=1.0, country='FO')
gc.add(name='ORNULF', gender='male', probability=1.0, country='NO')
gc.add(name='Ornulf', gender='male', probability=1.0, country='NO')
gc.add(name='Mykhailo', gender='male', probability=1.0, country='UA')
# Typo of Todd, probably
gc.add(name='Tood', gender='male', probability=1.0, country='US')
gc.add(name='Ushesh', gender='male', probability=1.0, country='US')
gc.add(name='Geghanush', gender='female', probability=1.0, country='AM')
gc.add(name='Bhadrika', gender='female', probability=1.0)
gc.add(name='ABDOLMAJID', gender='male', probability=1.0, country='IR')
gc.add(name='Momammad Reza', gender='male', probability=1.0, country='IR')
gc.add(name='Fazio', gender='male', probability=1.0, country='IT')
gc.add(name='Misak', gender='male', probability=1.0, country='AM')
gc.add(name='Tsolak', gender='male', probability=1.0, country='AM')
gc.add(name='Immo', gender='male', probability=1.0, country='DE')
gc.add(name='LOTFOLLAH', gender='male', probability=1.0, country='IR')
gc.add(name='But', gender='female', probability=1.0)
gc.add(name='Shteryo', gender='male', probability=1.0, country='BG')
gc.add(name='Zilvinas', gender='male', probability=1.0, country='LT')
gc.add(name='Primoz', gender='male', probability=1.0, country='SI')
gc.add(name='Andraz', gender='male', probability=1.0, country='SI')
gc.add(name='Cristián', gender='male', probability=1.0, country='DE')
gc.add(name='Hirokazu', gender='male', probability=1.0)
gc.add(name='Mihnea', gender='male', probability=1.0)
gc.add(name='Sandoche', gender='male', probability=1.0, country='FR')
gc.add(name='Ivanas', gender='male', probability=1.0)
gc.add(name='Takehito', gender='male', probability=1.0, country='JP')
gc.add(name='Katsumasa', gender='male', probability=1.0, country='JP')
gc.add(name='Eiichiro', gender='male', probability=1.0, country='JP')
gc.add(name='Smahena', gender='female', probability=1.0)
gc.add(name='Saloumeh', gender='female', probability=1.0)
gc.add(name='Heiki', gender='male', probability=1.0, country='EE')
gc.add(name='Barbulescu', gender='female', probability=1.0)
gc.add(name='Valeriu', gender='male', probability=1.0, country='RO')
gc.add(name='Curon', gender='male', probability=1.0)
gc.add(name='Géza', gender='male', probability=1.0, country='HU')
gc.add(name='Sergiusz', gender='male', probability=1.0)
gc.add(name='Mohammadali', gender='male', probability=1.0, country='IR')
gc.add(name='Naotake', gender='male', probability=1.0, country='JP')
gc.add(name='Taryk', gender='male', probability=1.0, country='PL')
gc.add(name='Marceli', gender='male', probability=1.0, country='PL')
gc.add(name='Ignacy', gender='male', probability=1.0, country='PL')
gc.add(name='Oleh', gender='male', probability=1.0, country='UA')
gc.add(name='Batsuren', gender='female', probability=1.0)
gc.add(name='Hamlesh', gender='male', probability=1.0)
gc.add(name='Temoor', gender='male', probability=1.0)
gc.add(name='Nkemdilim', gender='male', probability=1.0, country='NG')
gc.add(name='Lubor', gender='male', probability=1.0, country='SK')
gc.add(name='IJsbrand', gender='male', probability=1.0, country='BE')
gc.add(name='IJsbrand', gender='male', probability=1.0, country='NL')
gc.add(name='Normen', gender='male', probability=1.0, country='DE')
gc.add(name='Sevdalina', gender='female', probability=1.0, country='DE')
gc.add(name='Bendert', gender='male', probability=1.0, country='GB')
gc.add(name='Rayappa', gender='male', probability=1.0, country='IN')
gc.add(name='Neriah', gender='male', probability=1.0)
gc.add(name='Ernstjan', gender='male', probability=1.0, country='NL')
gc.add(name='Tijmen', gender='male', probability=1.0, country='NL')
gc.add(name='Sjaak', gender='male', probability=1.0, country='NL')
gc.add(name='Julf', gender='male', probability=1.0, country='NL')
gc.add(name='Julf', gender='male', probability=1.0, country='FI')
gc.add(name='Damiao', gender='male', probability=1.0)
gc.add(name='Yuliy', gender='male', probability=1.0, country='BG')
gc.add(name='Claerwen', gender='female', probability=1.0)
gc.add(name='Panait', gender='male', probability=1.0, country='RO')
gc.add(name='Kseniia', gender='female', probability=1.0)
gc.add(name='Filippe', gender='male', probability=1.0)
gc.add(name='Zoryana', gender='female', probability=1.0, country='UA')
gc.add(name='Aijay', gender='male', probability=1.0, country='US')
gc.add(name='Bedřich', gender='male', probability=1.0, country='CZ')
gc.add(name='Sando', gender='female', probability=1.0)
gc.add(name='Witalij', gender='male', probability=1.0)
gc.add(name='Mitalee', gender='female', probability=1.0)
gc.add(name='Aliasghar', gender='male', probability=1.0, country='IR')
gc.add(name='Gudvardur', gender='male', probability=1.0, country='IS')
gc.add(name='Ruaidhri', gender='male', probability=1.0)
gc.add(name='Lousewies', gender='female', probability=1.0)
gc.add(name='Gonçal', gender='male', probability=1.0, country='ES')
gc.add(name='Narseo', gender='male', probability=1.0, country='ES')
gc.add(name='Henrica', gender='male', probability=1.0, country='NL')
gc.add(name='Serhii', gender='male', probability=1.0, country='UA')
gc.add(name='Ievgenii', gender='male', probability=1.0, country='UA')
# Typo of John
gc.add(name='Johhn', gender='male', probability=1.0, country='US')
gc.add(name='Tsolak', gender='male', probability=1.0)
gc.add(name='Esime', gender='female', probability=1.0)
gc.add(name='Zsombor', gender='male', probability=1.0)
gc.add(name='Vladimer', gender='male', probability=1.0)
gc.add(name='Rinalia', gender='female', probability=1.0)
gc.add(name='Yevheniia', gender='female', probability=1.0, country='UA')

# *RIPE 75 names*
# https://www.behindthename.com/name/vahan
gc.add(name='Vahan', gender='male', probability=1.0)
# https://www.babynamesdirect.com/boy/hadif
gc.add(name='Hadif', gender='male', probability=1.0, country='AE')
# https://www.behindthename.com/name/sayed/submitted
gc.add(name='Osayed', gender='male', probability=1.0, country='AE')
# https://www.babycenter.com/baby-names-hannaneh-391505.htm
gc.add(name='Hannaneh', gender='female', probability=1.0)
# https://en.wikipedia.org/wiki/Avetik
gc.add(name='Avetik', gender='male', probability=1.0, country='AM')
# https://www.behindthename.com/name/karoli10na
gc.add(name='Karolína', gender='female', probability=1.0, country='CZ')
# https://www.behindthename.com/name/seyed
gc.add(name='SeyedAlireza', gender='male', probability=1.0, country='IR')
# https://www.babycenter.com/baby-names-zaineh-1154055.htm
gc.add(name='Zaineh', gender='female', probability=1.0, country='JO')
# https://www.babycenter.com/baby-names-musallam-1475482.htm
gc.add(name='Musallam', gender='male', probability=1.0)
# https://twitter.com/VymalaThuron
gc.add(name='Vymala', gender='female', probability=1.0, country='MU')

# *RIPE 76 names*
# https://www.behindthename.com/name/aleksandrina
gc.add(name='Aleksandrina', gender='female', probability=1.0, country='BG')
# https://www.behindthename.com/name/valenti10n
gc.add(name='Valentín', gender='male', probability=1.0, country='ES')
# http://www.babynamescience.com/baby-name/Akela-girl
gc.add(name='Akéla', gender='female', probability=1.0, country='FR')
# https://www.behindthename.com/name/the10odore
gc.add(name='Théodore', gender='male', probability=1.0, country='FR')
# Fédéric is Frederick, right?
gc.add(name='Fédéric', gender='male', probability=1.0, country='FR')
# https://www.behindthename.com/name/gae12l
gc.add(name='Gaël', gender='male', probability=1.0, country='FR')
# Mohammad is a male name
gc.add(name='MohammadAli', gender='male', probability=1.0, country='IR')
# http://hamariweb.com/names/muslim/persian/girl/mahrokh-meaning_6936
gc.add(name='Mahrokh', gender='female', probability=1.0, country='IR')
# Every MIchikazu on Facebook or Twitter is male
gc.add(name='MIchikazu', gender='male', probability=1.0, country='JP')
# https://www.behindthename.com/name/hideyuki/submitted
gc.add(name='Hideyuki', gender='male', probability=1.0)
# http://www.babynology.com/name/andjelko-m.html
gc.add(name='Andjelko', gender='male', probability=1.0)
# https://nameberry.com/babyname/Radhiya
gc.add(name='Radhiya', gender='female', probability=1.0, country='OM')
# met in person
gc.add(name='Rhisa', gender='female', probability=1.0, country='US')

def guess_genders(*, gendercache, names, country=''):
    """
    Guess the genders of every name in the names array, based on the
    given country (or no country if country is "XX" or "")

    Returns a hash with "xx" and "xy" as numbers, and "unknown" as a
    list of all unknown names.
    """
    xy_sum = 0.0
    xx_sum = 0.0
    unknown_gender = []
    while names:
        query_names = names[0:10]
        names = names[10:]
        if country in ('XX', ''):
            note = " (without country)"
            probabilities = gendercache.get(query_names)
        else:
            note = ""
            probabilities = gendercache.get(query_names, country_id=country)
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
                print("%.2f  %s %s%s" % (manliness, symbol, name, note))
            else:
                unknown_gender.append(gender_info['name'])

    return {"xy": xy_sum, "xx": xx_sum, "unknown": unknown_gender}


def get_split_names(names):
    """
    Convert any name with a '-' or whitespace in it to only the first
    part. So, "Gert-Jan" becomes "Gert" and "Anne Marie" becomes "Anne".

    Returns unchanged and changed names.
    """
    new_names = []
    old_names = []
    for name in names:
        if ' ' in name:
            new_names.append(name.split()[0])
        elif '-' in name:
            new_names.append(name.split('-')[0])
        else:
            old_names.append(name)
    return new_names, old_names


for file_name in sys.argv[1:]:
    mtg_id = re.sub(r'^([A-Z]+)(\d+)-.*$', r'\g<1> \g<2>', file_name.upper())
    mtg_name = re.sub(r' \d+$', '', mtg_id).lower()

    print("--- %s ----------------" % mtg_id, flush=True)

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
    for country, names in sorted(first_names_by_country.items()):
        print("== Country '%s' ==" % country, flush=True)
        info_by_country = guess_genders(gendercache=gc, names=names,
                                        country=country)
        xy_sum += info_by_country['xy']
        xx_sum += info_by_country['xx']
        if info_by_country["unknown"]:
            unknown_names = info_by_country['unknown']
            info_without_country = guess_genders(gendercache=gc,
                                                 names=unknown_names)
            xy_sum += info_without_country['xy']
            xx_sum += info_without_country['xx']
            if info_without_country["unknown"]:
                (split_names,
                 unknown) = get_split_names(info_without_country["unknown"])
                if split_names:
                    split_by_country = guess_genders(gendercache=gc,
                                                     names=split_names,
                                                     country=country)
                    xy_sum += split_by_country['xy']
                    xx_sum += split_by_country['xx']
                    if split_by_country['unknown']:
                        split_unknown = split_by_country['unknown']
                        last_guess = guess_genders(gendercache=gc,
                                                   names=split_unknown)
                        xy_sum += last_guess['xy']
                        xx_sum += last_guess['xx']
                        unknown.extend(last_guess['unknown'])
                na_sum += len(unknown)
                for unknown_name in unknown:
                    print("-.--  ? %s" % unknown_name, flush=True)

    with open(mtg_name + '-genders.csv', 'a', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, dialect='unix')
        writer.writerow((mtg_id,
                         "%.2f" % xy_sum,
                         "%.2f" % xx_sum,
                         "%.2f" % na_sum))

print("cache hits: %d, cache misses: %d" % (gc.hits, gc.misses), flush=True)
gc.save()
