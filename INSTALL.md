## Prepare enviroment
We will use PostgreSQL server even though our framework supports many...
That's because this project has some SQL code PostgreSQL specific.
### Dependencies:

```
python (version 2)
python-psycopg2	(postgresql module)
python-magic
Django python Web Framework version 1.6
mono 2.10 +
OpenRA.Utility and OpenRA.Lint
django-registration module (easy_install -Z django-registration)
sendmail
```

 * Run PostgreSQL server; create user and database (in utf-8 encoding)
 * Change password for postgres user; setup DB backups
 * Create new user for web site in your unix system
 * Django web server user must have .openra directory in it's home and have owner rights to it (for OpenRA.Utility)
 * Directory with compiled OpenRA tools must have write permissions for Django web server user
 * This repository root is actually a Django Site with additional Apps

### Edit Django settings.py (systemTool/settings.py)

 * Generate a new Django secret key and change "SECRET_KEY" setting
 * Change "DEBUG" setting to False if it's True
 * Modify "OPENRA_PATH" to specify a directory with compiled OpenRA files (with slash at the end) (make sure it's always the latest release)
 * Edit DB related configuration

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
    }
}
```

### Finish work with django:
 * Initialize datebase (this will create all tables). You'll get a prompt asking you if you'd like to create a superuser account for the authentication system. Go ahead and do that:

```
python manage.py syncdb
```

### Setup WebServer, URLs, RewriteRules, etc.
  

