## Prepare enviroment
We will use PostgreSQL server even though our framework supports many...
That's just our preference, so if you deploy it, you can choose any Database you want.
### Dependencies

```
python (version 2)
python-psycopg2  (postgresql module)
python-magic (pip install python-magic)
python-openid
python-requests
python-requests-oauthlib
Django python Web Framework version 1.6
mono 2.10 +
OpenRA.Utility and OpenRA.Lint
django-registration module (easy_install -Z django-registration)
django-allauth (pip install django-allauth)
sendmail (or any other mail server)
curl
```

 * Run PostgreSQL server; create user and database (in utf-8 encoding)
 * Change password for postgres user; setup DB backups
 * Create new user for web site in your unix system
 * Django web server user must have .openra directory in it's home and have owner rights to it (for OpenRA.Utility)
 * Directory with compiled OpenRA tools must have write permissions for Django web server user
 * Make sure Django web server user can write into '/tmp/'
 * This repository root is actually a Django Site with additional Apps

### Edit Django settings.py (systemTool/settings.py)

 * Generate a new Django secret key and change "SECRET_KEY" setting
 * Change "DEBUG" setting to False if it's True
 * Modify "OPENRA_PATH" to specify a directory with compiled OpenRA files (with slash at the end) (make sure it's always the latest release)
 * Modify "RSYNC_MAP_PATH" and "RSYNC_MAP_API_PATH" to specify directories where maps will be dumped by website trigger for dedicated servers and Map API mirrors usage. See [Sync Maps over Rsync](https://github.com/OpenRA/OpenRA-Content-Engine/wiki/Sync-maps-over-RSYNC-%28for-dedicated-servers%29) guide for details.
 * Modify GITHUB related settings (user, repository and API token): used to post an issue with info about OpenRA crash report
 * Modify "ADMIN_EMAIL" to specify an email address of a person who is responsible for fixing map uploading issues
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

### Finish work with django
 * Initialize database (this will create all tables). You'll get a prompt asking you if you'd like to create a superuser account for the authentication system. Go ahead and do that:

```
python manage.py syncdb
```

### Setup Production (using nginx + gunicorn)
All-sufficient guide: http://goodcode.io/blog/django-nginx-gunicorn/

Running gunicorn (WSGI HTTP Server) this way (10 instances, max timeout 30 seconds):

```
gunicorn_django -w 10 -t 30 --log-file=/path/to/djangoserver.log -b 127.0.0.1:8000
```

Nginx config for our virtual host (replace PATH where needed):

```
server {
        listen 80;
        server_name resource.openra.net;
        access_log /path/to/access.log;
        error_log /path/to/error.log;

        root /path/to/our/django/site/;
        location /static/ { # STATIC_URL
                alias /path/to/our/primary/application/static/; # STATIC_ROOT
                expires 30d;
        }

        location /media/ { # MEDIA_URL
                alias /path/to/our/primary/application/static/; # MEDIA_ROOT
                expires 30d;
         }
        location /static/admin/ {
                alias /usr/local/lib/python2.7/dist-packages/django/contrib/admin/static/admin/;
        }
        location / {
                proxy_pass_header Server;
                proxy_set_header Host $http_host;
                proxy_redirect off;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Scheme $scheme;
                proxy_connect_timeout 10;
                proxy_read_timeout 120;
                proxy_pass http://127.0.0.1:8000/;
        }
}
```

### Post-Installation
#### Configure allauth
 * Create an application at Github (callback url: http://yoursitedomain.com/accounts/github/login/callback/)
 * Go to your site admin page; "Sites" (django.contrib.sites application); create a site with a proper domain name
 * Go to "Social Apps"; Add a new social app (set a proper client id and secret, chose a proper site)
 * Load http://yoursitedomain.com/accounts/github/login/  to authorize your new application at github
 * Do the similar actions to create and set up Google Application (without creating new site over django admin)