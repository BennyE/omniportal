
# OmniPortal

OmniPortal - a Flask-based portal that intends to simply the creation of Guests &amp; Employees in Alcatel-Lucent Enterprise OmniVista.
The idea is that OmniPortal can be hosted on Alcatel-Lucent Enterprise OmniSwitch with AOS Release 8 in the future.

## Run OmniPortal (locally on your machine)

There are a couple of additional things that need to be done for the OmniSwitch, e.g. updating the paths to /flash/python/
This is work-in-progress, so expect rough edges!
`python3 -m flask --app omniportal --debug run --host 0.0.0.0 --port 5001`

## i18n

Edit the **messages.po** in the **translations/DE/LC_MESSAGES** or **translations/ES/LC_MESSAGES**
`.venv/bin/pybabel extract -F babel.cfg -k _l -o messages.pot .`
`.venv/bin/pybabel update -i messages.pot -d translations`
`.venv/bin/pybabel compile -d translations`
