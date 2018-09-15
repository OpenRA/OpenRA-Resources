```
Developed using:
	Python 3.4.2
	Django 1.9.4
	Database is PostgreSQL 9.4
	Mail server is exim4.84-8 # for outgoing emails
```



### System Dependencies

```
python3
python3-dev # is required to install some packages like psycopg2 via pip
imagemagick
```



### Set up virtualenv, example (using virtualenvwrapper):

```
$ pip install virtualenvwrapper
...
$ export WORKON_HOME=~/Envs
$ mkdir -p $WORKON_HOME
$ source /usr/local/bin/virtualenvwrapper.sh # path can differ
$ mkvirtualenv --python=/path/to/python3 resource_site
$ workon resource_site

# enter repository root directory and install python requirements:
$ pip install -r requirements.txt
```



### System configuration

 * Setup PostgreSQL server; create USER and DATABASE (Encoding: UTF-8)
 * Create new user for web site in your Linux system
 * Web site user must have ```.openra``` directory in it's home and have owner rights to it (for OpenRA.Utility)
 * Compile several OpenRA releases (directory names must match version tag), structure example:
```
	/home/openra/engines/
		/home/openra/engines/release-20151224/
		/home/openra/engines/release-20150919/
```
 * Compile OpenRA bleed version (directory name is any)
 * Create text file and put git hash of compiled bleed to it (Compiling bleed should be automated, like in production)
 * Directories with compiled OpenRA versions must have write permissions for web site user
 * Make sure web site user can write into '/tmp/'
 * Copy installed OpenRA Content from your local /home/user/.openra/Content/ to the same directory for web site user



### Edit openra/settings.py

 * Generate a new Django secret key and change "SECRET_KEY" setting
 * Change ```DEBUG``` setting to False if it's True
 * Modify ```ADMIN_EMAIL_FROM``` and ```ADMIN_EMAIL_TO``` to specify an email address of a person who is responsible for fixing map uploading issues
 * Edit Database connection settings
 * Change ```OPENRA_ROOT_PATH```, using example above, it will be ```/home/openra/engines/```
 * Change ```OPENRA_VERSIONS```, it will be just version tag names


### Initialize django database (this will create all tables)

```
python manage.py makemigrations && python manage.py makemigrations openra
python manage.py migrate
python manage.py createsuperuser
```

### Setup Production (using nginx + gunicorn)
* Using Apache is not advised
* Nginx + gunicorn guide: http://goodcode.io/blog/django-nginx-gunicorn/

Running gunicorn (WSGI HTTP Server) (10 instances, max timeout 300 seconds) in ```screen``` session:

```
screen -S resource_site
workon resource_site # see info about configuring virtualenv above
cd <repository root>
gunicorn openra.wsgi -w 10 -t 300 --log-file=/path/to/gunicorn.log -b 127.0.0.1:8000
```

Nginx config for our virtual host (replace path where required):

```
server {
		listen 80;
		client_max_body_size 100M;
		server_name resource.openra.net;
		access_log /path/to/access.log;
		error_log /path/to/error.log;

		root /path/to/our/django/repository_root/openra/; # with app name

		location /static/ { # STATIC_URL
				alias /path/to/our/primary/application/static/; # STATIC_ROOT
				expires 30d;
		}

		location = /favicon.ico {
				alias /path/to/our/primary/application/static/favicon.ico;
		}

		gzip on;
		gzip_disable "msie6";

		gzip_comp_level 6;
		gzip_min_length 1100;
		gzip_buffers 16 8k;
		gzip_proxied any;
		gzip_types
			text/plain
			text/css
			text/js
			text/xml
			text/javascript
			application/javascript
			application/x-javascript
			application/json
			application/xml
			application/xml+rss;

		location / {
				proxy_pass_header Server;
				proxy_set_header Host $http_host;
				proxy_redirect off;
				proxy_set_header X-Real-IP $remote_addr;
				proxy_set_header X-Scheme $scheme;
				proxy_connect_timeout 300;
				proxy_read_timeout 300;
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
