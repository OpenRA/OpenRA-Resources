## Prepare enviroment
We will use PostgreSQL server even though our framework supports many...
That's because this project has some SQL code PostgreSQL specific.
### Dependencies:
    python (version 2)
    python-psycopg2	(postgresql module)
    Django python Web Framework version 1.6

 * Run PostgreSQL server; create user and database (in utf-8 encoding)
 * Change password for postgres user; setup DB backups
 * Create new user for web site in your unix system

 * Initialize Django Site in directory you like:
   django-admin.py startproject contentEngine

 * Copy APPs you fetched from github into that directory (ex: into root of contentEngine)

### Edit Django settings.py (contentEngine/contentEngine/settings.py)
 * Add APPs you fetched, without touching existing Aplications
 * Edit DB related configuration
 * Add a path to templates

### Finish work with django:
 * Initialize datebase (this will create all tables):
   python manage.py syncdb

### Setup WebServer, URLs, RewriteRules, etc.
  
