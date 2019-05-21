all: getattendees.py getattendees-sql.py guessgender.py
	flake8 $^
