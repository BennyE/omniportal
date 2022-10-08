
[![Docker Repository on Quay](https://quay.io/repository/bennye_hh/omniportal/status "Docker Repository on Quay")](https://quay.io/repository/bennye_hh/omniportal)

# OmniPortal

OmniPortal - a Flask-based portal that intends to simply the creation of Guests &amp; Employees in Alcatel-Lucent Enterprise OmniVista.
The idea is that OmniPortal can be hosted on Alcatel-Lucent Enterprise OmniSwitch with AOS Release 8 in the future.

## Run OmniPortal

You have multiple options to run OmniPortal

### Run OmniPortal (locally on your machine)

There are a couple of additional things that need to be done for the OmniSwitch, e.g. updating the paths to /flash/python/
This is work-in-progress, so expect rough edges! **I strongly recommend to work with a .venv!**

`git clone https://github.com/BennyE/omniportal.git`

`python3 -m pip install -r requirements.txt`

`python3 -m flask --app omniportal --debug run --host 0.0.0.0 --port 5000`

- ~~You'll want to update your **app.secret_key** before you do anything else~~ (all automated in current build)
- Navigate to 127.0.0.1:5000 (you don't want to run **debug** if outside of development phase)
- Attempt to login with admin/admin123, the attempt will fail and inform you that "admin/admin123" account was created in **omniportal_users.json**
- Navigate to /admin and do your settings
- Change your password! Please don't use something valuable, as the **omniportal_users.json** stores this unencrypted (as of now)!

### Run OmniPortal in Docker (local build)

You'll find the files that store the configuration/settings in **/home/$USER/omniportal_conf/**

#### Build locally

`sudo docker build --tag omniportal:latest .`

#### Run OmniPortal

`sudo docker run --rm --name omniportal -v ~/omniportal_conf/:/usr/src/app/conf/ -p 5000:5000 -d omniportal:latest`

#### Optional: Run OmniPortal with --debug

`sudo docker run --rm --name omniportal -e EXTRA_OPTIONS="--debug" -v ~/omniportal_conf/:/usr/src/app/conf/ -p 5000:5000 -d omniportal:latest`

#### Stop OmniPortal-Docker

`sudo docker stop omniportal`

### Run OmniPortal (my image) from Quay.io

You'll find the files that store the configuration/settings in **/home/$USER/omniportal_conf/**

`sudo docker run --rm --name omniportal -v ~/omniportal_conf/:/usr/src/app/conf/ -p 5000:5000 -d quay.io/bennye_hh/omniportal:latest`

#### Stop OmniPortal-Docker

`sudo docker stop omniportal`

## i18n

Edit the **messages.po** in the **translations/de/LC_MESSAGES** or e.g. **translations/es/LC_MESSAGES**

### Extract (new) translatables into messages.pot

`.venv/bin/pybabel extract -F babel.cfg -k _l -o messages.pot .`

### Update the corresponding individual language files

`.venv/bin/pybabel update -i messages.pot -d translations`

### Compile the translation when translation-work is done

`.venv/bin/pybabel compile -d translations`

## TODO

1. "Guest" and "Admin"-role are the two only roles taken into account so far
2. There is no logic yet that handles "running on OmniSwitch with AOS R8"
3. No Adaptive Card is sent yet after creating the Employee account
4. Avaya OneCloud CPaaS (for e.g. SMS) is not implemented yet
5. The code could need some structuring into multiple files
6. Possibly it would make sense to move to sqlite instead of JSON files, to be evaluated later

## Recent Changes

1. Create app.secret_key, omniportal_users & omniportal_settings automatically if those don't exist and store in conf directory
2. Dockerfile & Quay.io (Thanks to https://github.com/dgo19 for the help!)

## Screenshot

![omniportal](https://user-images.githubusercontent.com/5174414/193449734-003135ea-279c-47f2-be88-0051321efc74.png)

