
# OmniPortal

OmniPortal - a Flask-based portal that intends to simply the creation of Guests &amp; Employees in Alcatel-Lucent Enterprise OmniVista.
The idea is that OmniPortal can be hosted on Alcatel-Lucent Enterprise OmniSwitch with AOS Release 8 in the future.

## Run OmniPortal (locally on your machine)

There are a couple of additional things that need to be done for the OmniSwitch, e.g. updating the paths to /flash/python/
This is work-in-progress, so expect rough edges! **I strongly recommend to work with a .venv!**

`python3 -m pip install -r requirements.txt`

`python3 -m flask --app omniportal --debug run --host 0.0.0.0 --port 5001`

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
