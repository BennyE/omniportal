from flask_bootstrap import Bootstrap5
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_babel import Babel, _
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, Regexp
from wtforms.fields import *
from wtforms.widgets import PasswordInput
import json
import requests
import functools
import time
import datetime
import random
import string
import os
import sys
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)

# Paths
op_secret_key = "conf/omniportal_secret_key.json"
op_userfile = "conf/omniportal_users.json"
op_settingsfile = "conf/omniportal_settings.json"

# Try to load a secret token, if it doesn't exist create it.
# This secures cookies and makes them unique to this installation.
try:
    with open(op_secret_key, "r") as secret_key_fh:
        token = json.loads(secret_key_fh.read())
except json.decoder.JSONDecodeError:
    with open(op_secret_key, "w") as secret_key_fh:
        import secrets
        token = {"token": secrets.token_hex()}
        secret_key_fh.write(json.dumps(token))
        os.chmod(op_secret_key, 0o600)
except FileNotFoundError:
    with open(op_secret_key, "w") as secret_key_fh:
        import secrets
        token = {"token": secrets.token_hex()}
        secret_key_fh.write(json.dumps(token))
        os.chmod(op_secret_key, 0o600)
except PermissionError:
    sys.exit(f"Permission denied to read/write {op_secret_key}")

secret_key_fh.close()
app.secret_key = token["token"]

# i18n - Translation to other languages
babel = Babel(app) 

# Beautify the app with Bootstrap5
bootstrap = Bootstrap5(app)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired(message=_l('The username doesn\'t meet the requirements')), Length(1, 64)])
    password = PasswordField(_l('Password'), validators=[DataRequired(message=_l('The password doesn\'t meet the requirements')), Length(8, 150)])
    submit = SubmitField(_l('Log In'))

class CreateUserForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired(message=_l('The username doesn\'t meet the requirements')), Length(1, 64)])
    password = PasswordField(_l('Password'), validators=[DataRequired(message=_l('The password doesn\'t meet the requirements')), Length(8, 150)])
    entitlement = SelectMultipleField(label=_l('Entitlement'), choices=[('admin', _l('Administrator')), ('guest', _l('Guests')), ('employee', _l('Employees'))], default='guest', validators=[DataRequired(message=_l('A selection is required!'))])
    submit = SubmitField(_l('Create User'))

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(_l('Current Password'), validators=[DataRequired(message=_l('The password doesn\'t meet the requirements')), Length(8, 150)])
    new_password = PasswordField(_l('New Password'), validators=[DataRequired(message=_l('The password doesn\'t meet the requirements')), Length(8, 150)])
    submit = SubmitField(_l('Change Password'))

class RemoveUserForm(FlaskForm):
    username = SelectField(_l('Username'))
    submit = SubmitField(_l('Remove User'))
    @classmethod
    def new(cls):
        form = cls()
        form.username.choices = get_usernames()
        return form

class ChangeSettings(FlaskForm):
    guest_operator_url = URLField(_l('OmniVista 2500 NMS / OmniVista Cirrus UPAM URL'), default="https://ov2500-upam-cportal.al-enterprise.com")
    guest_operator_username = StringField(_l('Guest Operator Username'), validators=[DataRequired(message=_l('The username doesn\'t meet the requirements')), Length(1, 32)])
    guest_operator_password = StringField(_l('Guest Operator Password'), validators=[DataRequired(message=_l('The password doesn\'t meet the requirements')), Length(6, 16)], widget=PasswordInput(hide_value=False))
    guest_prefix = StringField(_l('Guest Prefix'), validators=[DataRequired(message=_l('The guest prefix doesn\'t meet the requirements')), Length(1, 10)], default=_l('guest'))
    wifi_network = StringField(_l('Guest Wi-Fi / SSID Name'), validators=[DataRequired(message=_l('The Wi-Fi network / SSID name doesn\'t meet the requirements')), Length(1, 31)])
    ale_rainbow_webhook = StringField(_l('ALE Rainbow Webhook'), widget=PasswordInput(hide_value=False))
    ringcentral_webhook = StringField(_l('RingCentral / Rainbow Office Webhook'), widget=PasswordInput(hide_value=False))
    ms_teams_webhook = StringField(_l('Microsoft Teams Webhook'), widget=PasswordInput(hide_value=False))
    employee_prefix = StringField(_l('Employee Prefix'), default=_l('employee_'))
    employee_wifi = StringField(_l('Employee Wi-Fi / SSID Name'))
    ove_ovc_url = URLField(_l('OmniVista 2500 NMS / OmniVista Cirrus URL'), default='https://tenant-name.ov.ovcirrus.com')
    validate_ove_ovc_cert = RadioField(_l('Validate OmniVista 2500 NMS HTTPS certificate'), choices=[('yes', 'Yes'), ('no', 'No')], default='no')
    # Access via API key is currently not offered
    #ove_ovc_api_key = StringField(_l('OmniVista 2500 NMS / OmniVista Cirrus API Key'), widget=PasswordInput(hide_value=False))
    ove_ovc_username = StringField(_l('OmniVista 2500 NMS / OmniVista Cirrus Username'))
    ove_ovc_password = StringField(_l('OmniVista 2500 NMS / OmniVista Cirrus Password'), widget=PasswordInput(hide_value=False))
    submit = SubmitField(_l('Save Settings'))
    @classmethod
    def new(cls):
        form = cls()
        settings = read_settings()
        try:
            form.guest_operator_url.data = settings["guest_operator_url"]
            form.guest_operator_username.data = settings["guest_operator_username"]
            form.guest_operator_password.data = settings["guest_operator_password"]
            form.guest_prefix.data = settings["guest_prefix"]
            form.ale_rainbow_webhook.data = settings["ale_rainbow_webhook"]
            form.ringcentral_webhook.data = settings["ringcentral_webhook"]
            form.ms_teams_webhook.data = settings["ms_teams_webhook"]
            form.employee_prefix.data = settings["employee_prefix"]
            form.wifi_network.data = settings["wifi_network"]
            form.employee_wifi.data = settings["employee_wifi"]
            form.ove_ovc_url.data = settings["ove_ovc_url"]
            form.validate_ove_ovc_cert.data = settings["validate_ove_ovc_cert"]
            #form.ove_ovc_api_key.data = settings["ove_ovc_api_key"]
            form.ove_ovc_username.data = settings["ove_ovc_username"]
            form.ove_ovc_password.data = settings["ove_ovc_password"]
        except KeyError:
            pass
        return form

class AddGuestForm(FlaskForm):
    #username = StringField(_l('Username'), validators=[DataRequired(message=_l('The username doesn\'t meet the requirements')), Length(1, 128)])
    username = StringField(_l('Username'), validators=[Regexp(r'^[0-9a-zA-Z/\.\-:_@\S]+$', message=_l('The field can only contain 0-9 a-z A-Z / . - : _ @')), Length(1, 128)])
    # I don't think that anybody would want to specify the password manually
    #password = PasswordField(_l('Password'), validators=[DataRequired(message=_l('The password doesn\'t meet the requirements')), Length(6, 16)])
    valid_until = DateField(label=_l('Valid Until'), description=_l('Select the day until when the account should be valid!'))
    submit = SubmitField(label=_l('Create Guest'))

class AddEmployeeForm(FlaskForm):
    #username = StringField(_l('Username'), validators=[Regexp(r'^[0-9a-zA-Z/\.\-:_@\S]+$', message=_l('The field can only contain 0-9 a-z A-Z / . - : _ @')), Length(1, 32)])
    email = StringField(_l('Email'), validators=[DataRequired(message=_l('The field can only contain 0-9 a-z A-Z / . - : _ @')), Length(4, 64)])
    #telephone = StringField(_l('Mobile'), validators=[DataRequired(message=_l('The field can only contain 0-9 +')), Length(4, 18)])
    submit = SubmitField(label=_l('Create Employee'))

class TestGuestForm(FlaskForm):
    username = StringField(_l('Username'), validators=[Regexp(r'^[0-9a-zA-Z/\.\-:_@\S]+$', message=_l('The field can only contain 0-9 a-z A-Z / . - : _ @')), Length(1, 128)])
    submit = SubmitField(label=_l('Create Guest'))

class QuickGuestForm(FlaskForm):
    one_day = SubmitField(_l('1 Day'))
    three_days = SubmitField(_l('3 Days'))
    five_days = SubmitField(_l('5 Days'))
    seven_days = SubmitField(_l('7 Days'))
    fourteen_days = SubmitField(_l('14 Days'))
    thirty_days = SubmitField(_l('30 Days'))

@babel.localeselector
def get_locale():
    available_translations = ["de", "en"]
    # "en" is the default
    locale = "en"
    for lang in request.accept_languages.values():
        if lang[:2] in available_translations:
            locale = lang[:2]
            break
    g.locale = locale
    return locale

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or (g.entitlement is None or "admin" not in g.entitlement):
            return redirect(url_for('login'))

        return view(**kwargs)

    return wrapped_view

def guest_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        elif g.entitlement is None:
            return redirect(url_for('login'))
        elif ("guest" not in g.entitlement) and ("admin" not in g.entitlement):
            return redirect(url_for('login'))

        return view(**kwargs)

    return wrapped_view

def employee_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        elif g.entitlement is None:
            return redirect(url_for('login'))
        elif ("employee" not in g.entitlement) and ("admin" not in g.entitlement):
            return redirect(url_for('login'))

        return view(**kwargs)

    return wrapped_view

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))

        return view(**kwargs)

    return wrapped_view

def get_usernames():
    try:
        with open(op_userfile, "r") as op_users:
            users = json.loads(op_users.read())
            choices = []
            for user in users.keys():
                choices.append((user, user))
            return choices
    except json.decoder.JSONDecodeError:
        pass

def check_for_undesireable_words(input):
    # You may need to adapt this to your local language
    undesireable_words = ["cunt", "pussy", "nigger", "penis", "fotze", "hitler", "fuck"]

    for uw in undesireable_words:
        if uw in input.lower():
            return True
    return False

def generate_admin_password():
    # Doesn't contain "l", "I", "O", "0" and "1" on purpose to avoid mistyping, thx Michael
    letters = "ABCDEFGHJKMNPQRSTUVWXYZ23456789abcdefghijkmnopqrstuvwxyz"
    try:
        r = random.SystemRandom()
    except NotImplementedError as nie:
        print(nie)
        flash(_("Your system doesn't provide a secure random generator!"))
        return False

    # Generate a reasonable secure random password for Admin Accounts
    random_password = "".join(r.choice(letters) for _ in range(16))
    
    while check_for_undesireable_words(random_password):
        print("Found an undesireable word in password string, generating new one!")
        random_password = "".join(r.choice(letters) for _ in range(16))
    return random_password

def create_default_op_users():
    with open(op_userfile, "w") as op_users:
        default_user = {}
        random_password = generate_admin_password()
        default_user["admin"] = {"password":pbkdf2_sha256.hash(random_password), "entitlement":["admin"]}
        op_users.write(json.dumps(default_user))
        os.chmod(op_userfile, 0o600)
    return random_password

def create_op_user(new_user, password, entitlements):
    with open(op_userfile, "r") as op_users:
        users = json.loads(op_users.read())
        if new_user in users.keys():
            return False
    with open(op_userfile, "w") as op_users:
        final_entitlements = []
        for entitlement in entitlements:
            final_entitlements.append(entitlement)
        users[new_user] = {"password":pbkdf2_sha256.hash(password), "entitlement":final_entitlements}
        op_users.write(json.dumps(users))
        return True

def remove_op_user(username):
    with open(op_userfile, "r") as op_users:
        users = json.loads(op_users.read())
        if username == g.user:
            return False
        elif username not in users.keys():
            return False
    with open(op_userfile, "w") as op_users:
        users.pop(username)
        op_users.write(json.dumps(users))
        return True

def change_op_password(username, password, new_password):
    with open(op_userfile, "r") as op_users:
        users = json.loads(op_users.read())
        if not pbkdf2_sha256.verify(password, users[username]["password"]):
            return False
    with open(op_userfile, "w") as op_users:
        users[username]["password"] = pbkdf2_sha256.hash(new_password)
        op_users.write(json.dumps(users))
        return True

def create_default_op_settings():
    try:
        with open(op_settingsfile, "w") as settings_fh:
            default_settings = {
                "guest_operator_url": "https://ov2500-upam-cportal.al-enterprise.com", 
                "guest_operator_username": "", 
                "guest_operator_password": "", 
                "guest_prefix": "guest", 
                "wifi_network": "", 
                "ale_rainbow_webhook": "", 
                "ringcentral_webhook": "", 
                "ms_teams_webhook": "", 
                "employee_prefix": "",
                "employee_wifi": "",
                "ove_ovc_url": "", 
                "validate_ove_ovc_cert": "no", 
                "ove_ovc_username": "",
                "ove_ovc_password": ""
            }
            settings_fh.write(json.dumps(default_settings))
            os.chmod(op_settingsfile, 0o600)
    except PermissionError:
        sys.exit(f"Permission denied to read/write {op_settingsfile}")
    return default_settings

def read_settings():
    try:
        with open(op_settingsfile, "r") as settings:
            setting = json.loads(settings.read())
            if setting["validate_ove_ovc_cert"] == "yes":
                setting["check_certs"] = True
            else:
                setting["check_certs"] = False
    except json.decoder.JSONDecodeError:
        setting = create_default_op_settings()
    except FileNotFoundError:
        setting = create_default_op_settings()
    return setting

def save_settings(guest_operator_url, guest_operator_username, guest_operator_password, guest_prefix, wifi_network,
                    ale_rainbow_webhook, ringcentral_webhook, ms_teams_webhook, ove_ovc_url, validate_ove_ovc_cert,
                    employee_wifi, employee_prefix, ove_ovc_username, ove_ovc_password):
    with open(op_settingsfile, "w") as settings:
        setting = {}
        setting["guest_operator_url"] = guest_operator_url.rstrip("/")
        setting["guest_operator_username"] = guest_operator_username
        setting["guest_operator_password"] = guest_operator_password
        setting["guest_prefix"] = guest_prefix
        setting["wifi_network"] = wifi_network
        setting["ale_rainbow_webhook"] = ale_rainbow_webhook
        setting["ringcentral_webhook"] = ringcentral_webhook                
        setting["ms_teams_webhook"] = ms_teams_webhook
        setting["ove_ovc_url"] = ove_ovc_url.rstrip("/")
        setting["validate_ove_ovc_cert"] = validate_ove_ovc_cert
        #setting["ove_ovc_api_key"] = ove_ovc_api_key
        setting["employee_wifi"] = employee_wifi
        setting["employee_prefix"] = employee_prefix
        setting["ove_ovc_username"] = ove_ovc_username
        setting["ove_ovc_password"] = ove_ovc_password
        settings.write(json.dumps(setting))
    return True

def valid_login(username, password):
    try:
        with open(op_userfile, "r") as op_users:
            users = json.loads(op_users.read())
            for user, values in users.items():
                if user == username and pbkdf2_sha256.verify(password, values["password"]):
                    return True
    except FileNotFoundError:
        random_password = create_default_op_users()
        flash(_('Default credentials created: admin/%s(pw) to login!', pw=random_password), 'success')
        return False

def log_the_user_in(username):
    try:
        with open(op_userfile, "r") as op_users:
            users = json.loads(op_users.read())
    except FileNotFoundError:
        pass
    session["user_id"] = username
    session["entitlement"] = users[username]["entitlement"]
    return redirect(url_for('index'))

@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    entitlement = session.get("entitlement")
    if user_id is None:
        g.user = None
        g.entitlement = None
    else:
        g.user = user_id
        g.entitlement = entitlement

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin", methods=["POST", "GET"])
@admin_required
def admin():
    # if request.method == "GET" and g.entitlement == "admin":
    #     return render_template("create_user.html")
    #error = None
    form = ChangeSettings.new()
    if request.method == "POST" and "admin" in g.entitlement:
        if save_settings(request.form["guest_operator_url"],
                         request.form["guest_operator_username"],
                         request.form["guest_operator_password"],
                         request.form["guest_prefix"],
                         request.form["wifi_network"],
                         request.form["ale_rainbow_webhook"],
                         request.form["ringcentral_webhook"],
                         request.form["ms_teams_webhook"],
                         request.form["ove_ovc_url"],
                         request.form["validate_ove_ovc_cert"],
                         #request.form["ove_ovc_api_key"]
                         request.form["employee_wifi"],
                         request.form["employee_prefix"],
                         request.form["ove_ovc_username"],
                         request.form["ove_ovc_password"]
                         ):
            flash(_('The settings were saved!'), 'success')
            return redirect(url_for('index'))
        else:
            #error = _l("Invalid username/password")
            #print(error)
            flash(_('Something went wrong!'), 'danger')
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template("change_settings.html", form=form)

@app.route("/create_user", methods=["POST", "GET"])
@admin_required
def create_user():
    # if request.method == "GET" and g.entitlement == "admin":
    #     return render_template("create_user.html")
    #error = None
    form = CreateUserForm()
    if request.method == "POST" and "admin" in g.entitlement:
        if create_op_user(request.form["username"],
                          request.form["password"],
                          request.form.getlist("entitlement")):
            flash(_('The user was successfully created!'), 'success')
            return redirect(url_for('index'))
        else:
            #error = _l("Invalid username/password")
            #print(error)
            flash(_('The user you try to create already exists!'), 'danger')
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template("create_user.html", form=form)

@app.route("/change_password", methods=["POST", "GET"])
@login_required
def change_password():
    # if request.method == "GET" and g.entitlement == "admin":
    #     return render_template("create_user.html")
    #error = None
    form = ChangePasswordForm()
    if request.method == "POST":
        if change_op_password(g.user,
                              request.form["current_password"],
                              request.form["new_password"]):
            flash(_('The password was updated!'), 'success')
            return redirect(url_for('index'))
        else:
            #error = _l("Invalid username/password")
            #print(error)
            flash(_('The password wasn\'t updated!'), 'danger')
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template("change_password.html", form=form)

@app.route("/remove_user", methods=["POST", "GET"])
@admin_required
def remove_user():
    # if request.method == "GET" and g.entitlement == "admin":
    #     return render_template("create_user.html")
    #error = None
    form = RemoveUserForm.new()
    if request.method == "POST":
        if remove_op_user(request.form["username"]):
            flash(_('The user was removed!'), 'success')
            return redirect(url_for('index'))
        else:
            #error = _l("Invalid username/password")
            #print(error)
            flash(_('You cannot delete yourself!'), 'danger')
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template("remove_user.html", form=form)

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET" and g.user:
        return redirect(url_for('index'))
    #error = None
    form = LoginForm()
    if request.method == "POST":
        if valid_login(request.form["username"],
                       request.form["password"]):
            flash(_('Login successful!'), 'success')
            return log_the_user_in(request.form["username"])
        else:
            #error = _l("Invalid username/password")
            #print(error)
            flash(_('Invalid username/password!'), 'danger')
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    # remove the username from the session if it's there
    session.pop("user_id", None)
    session.pop("entitlement", None)
    session.clear()
    return redirect(url_for("index"))

def get_guest_accounts():
    settings = read_settings()
    req = requests.Session()
    login_header = {
        "Content-Type":"application/json"
    }
    login_data = {
        "username":settings['guest_operator_username'],
        "password":settings['guest_operator_password'],
        "identity":"Guest"
    }
    resp_login = req.post(f"{settings['guest_operator_url']}/sponsor/api/ham/guest/manager/judge", headers=login_header, json=login_data)
    print("LOGIN: ", resp_login.status_code, resp_login.reason, resp_login.json())
    if resp_login.json()['errorCode'] != 0:
        flash(_('Login to OmniVista UPAM failed! Wrong username or password!'), 'danger')
        return False
    account_data = {
        "queryBy":"Account",
        "querySize":1000,
        "start":""
    }
    resp_accounts = req.post(f"{settings['guest_operator_url']}/sponsor/api/ham/guest/account/getPageAccountList", json=account_data)
    print("Accounts: ", resp_accounts.status_code, resp_accounts.reason)
    #print(json.dumps(resp_accounts.json(), indent=4))
    req.get(f"{settings['guest_operator_url']}/sponsor/api/ham/guest/manager/logout")
    return resp_accounts.json()

def get_employee_accounts():
    settings = read_settings()
    req = requests.Session()

    login_header = {
        "Content-Type":"application/json"
    }

    login_data = {
        "userName":settings['ove_ovc_username'],
        "password":settings['ove_ovc_password']
    }

    ov_login = req.post(f"{settings['ove_ovc_url']}/api/login", headers=login_header, json=login_data, verify=settings['check_certs'])
    print(ov_login.status_code, ov_login.reason, "OV Login - Employee Accounts")
    #print(ov_login.json())

    employee_data = {
        "start":"",
        "querySize":1000
    }
    resp_accounts = req.post(f"{settings['ove_ovc_url']}/api/ham/userAccount/getPageAllAccountList", headers=login_header, json=employee_data, verify=settings['check_certs'])
    #print("Accounts: ", resp_accounts.status_code, resp_accounts.reason)
    print(resp_accounts.status_code, resp_accounts.reason, "OV Query - Employee Accounts - DATA")

    ov_logout = req.get(f"{settings['ove_ovc_url']}/api/logout", headers=login_header, verify=settings['check_certs'])
    print(ov_logout.status_code, ov_logout.reason, "OV Logout - Employee Accounts")

    req.close()

    return resp_accounts.json()

def create_employee_account(username, email, telephone):
    settings = read_settings()
    req = requests.Session()
    login_header = {
        "Content-Type":"application/json",
        "Authorization": f"Bearer {settings['ove_ovc_api_key']}"
    }

    # You may need to adapt this to your local language
    undesireable_words = ["cunt", "pussy", "nigger", "penis", "fotze", "hitler", "fuck"]

    # Doesn't contain "l", "I", "O", "0" and "1" on purpose to avoid mistyping, thx Michael
    letters = "ABCDEFGHJKMNPQRSTUVWXYZ23456789abcdefghijkmnopqrstuvwxyz"
    try:
        r = random.SystemRandom()
    except NotImplementedError as nie:
        print(nie)
        flash(_("Your system doesn't provide a secure random generator!"))
        return False

    # Generate a secure random password for Guest Accounts
    random_password = "".join(r.choice(letters) for _ in range(16))

    for uw in undesireable_words:
        if uw in random_password.lower():
            print("[!] Detected undesirable word in password, generating a new one!")
            # I assume our chances are very low to generate two undesireable words in a row
            random_password = "".join(r.choice(letters) for _ in range(16))
            break
    
    employee_data = {
        "repeat":random_password,
        "otherAttributesVOs":[],
        "username":username,
        "password":random_password,
        "telephone":telephone,
        "email":email
    }
    print(employee_data)
    resp_create_employee = req.post(f"{settings['ove_ovc_url']}/api/ham/userAccount/addUser", headers=login_header, json=employee_data, verify=settings['check_certs'])
    print("Employee Account: ", resp_create_employee.status_code, resp_create_employee.reason)
    if resp_create_employee.json()['errorCode'] != 0:
        if resp_create_employee.json()['errorMessage'] == "upam.usernameRepeat":
            flash(_('An employee account with this username already exists!'))
            return False
        elif resp_create_employee.json()['errorMessage'] == "upam.parametersIllegal":
            flash(_('Illegal parameters given!'))
            return False
        else:
            flash(_("An error occured! Creating employee account failed!"))
    print(resp_create_employee.json())
    flash(_('The employee account was created!'), 'success')

def quick_guest_account(days):
    settings = read_settings()
    req = requests.Session()
    login_header = {
        "Content-Type":"application/json"
    }
    login_data = {
        "username":settings['guest_operator_username'],
        "password":settings['guest_operator_password'],
        "identity":"Guest"
    }
    resp_login = req.post(f"{settings['guest_operator_url']}/sponsor/api/ham/guest/manager/judge", headers=login_header, json=login_data)
    print("LOGIN: ", resp_login.status_code, resp_login.reason, resp_login.json())
    if resp_login.json()['errorCode'] != 0:
        flash(_('Login to OmniVista UPAM failed! Wrong username or password!'), 'danger')
        return False
    
    letters = string.ascii_lowercase
    random_username = ''.join(random.choice(letters) for _ in range(6))

    # You may need to adapt this to your local language
    undesireable_words = ["cunt", "pussy", "nigger", "penis", "fotze", "hitler", "fuck"]

    for uw in undesireable_words:
        if uw in random_username:
            print("[!] Detected undesirable word in username, generating a new one!")
            # I assume our chances are very low to generate two undesireable words in a row
            random_username = ''.join(random.choice(letters) for _ in range(6))
            break

    # Doesn't contain "l", "I", "O", "0" and "1" on purpose to avoid mistyping, thx Michael
    letters = "ABCDEFGHJKMNPQRSTUVWXYZ23456789abcdefghijkmnopqrstuvwxyz"
    try:
        r = random.SystemRandom()
    except NotImplementedError as nie:
        print(nie)
        flash(_("Your system doesn't provide a secure random generator!"))
        return False

    # Generate a secure random password for Guest Accounts
    random_password = "".join(r.choice(letters) for _ in range(6))

    for uw in undesireable_words:
        if uw in random_password.lower():
            print("[!] Detected undesirable word in password, generating a new one!")
            # I assume our chances are very low to generate two undesireable words in a row
            random_password = "".join(r.choice(letters) for _ in range(6))
            break
    
    guest_username = f"{settings['guest_prefix']}_{random_username}"
    valid_until = int(round((time.time() + (86400 * days)) * 1000))

    guest_data = {
        "creator":settings['guest_operator_username'],
        "accountType":"Account",
        "password":random_password,
        "repeat":random_password,
        "username":guest_username,
        "dataQuotaAmount":1000,
        "accountValidityPeriod":valid_until,
        "dataQuota":"Disabled",
        "description":f"OmniPortal - ExpressGuest by {g.user}"
    }

    resp_guest = req.post(f"{settings['guest_operator_url']}/sponsor/api/ham/guest/account/addAccount", json=guest_data)
    print("Accounts: ", resp_guest.status_code, resp_guest.reason)
    print(json.dumps(resp_guest.json(), indent=4))
    req.get(f"{settings['guest_operator_url']}/sponsor/api/ham/guest/manager/logout")
    if resp_guest.json()['errorCode'] != 0:
        if resp_guest.json()['errorMessage'] == "upam.accountNameRepeat":
            flash(_('An account with this username already exists!'))
            return False
    send_ms_teams_card(guest_username, random_password, datetime.datetime.fromtimestamp(valid_until / 1000).strftime("%d.%m.%Y, %H:%M:%S"))
    send_ringcentral_card(guest_username, random_password, datetime.datetime.fromtimestamp(valid_until / 1000).strftime("%d.%m.%Y, %H:%M:%S"))
    send_rainbow_card(guest_username, random_password, datetime.datetime.fromtimestamp(valid_until / 1000).strftime("%d.%m.%Y, %H:%M:%S"))
    flash(_('The guest account was created!'), 'success')

def create_guest_account(guest_name, valid_until):
    settings = read_settings()
    req = requests.Session()
    login_header = {
        "Content-Type":"application/json"
    }
    login_data = {
        "username":settings['guest_operator_username'],
        "password":settings['guest_operator_password'],
        "identity":"Guest"
    }
    resp_login = req.post(f"{settings['guest_operator_url']}/sponsor/api/ham/guest/manager/judge", headers=login_header, json=login_data)
    print("LOGIN: ", resp_login.status_code, resp_login.reason, resp_login.json())
    if resp_login.json()['errorCode'] != 0:
        flash(_('Login to OmniVista UPAM failed! Wrong username or password!'), 'danger')
        return False
    
    # You may need to adapt this to your local language
    undesireable_words = ["cunt", "pussy", "nigger", "penis", "fotze", "hitler", "fuck"]

    # Doesn't contain "l", "I", "O", "0" and "1" on purpose to avoid mistyping, thx Michael
    letters = "ABCDEFGHJKMNPQRSTUVWXYZ23456789abcdefghijkmnopqrstuvwxyz"
    try:
        r = random.SystemRandom()
    except NotImplementedError as nie:
        print(nie)
        flash(_("Your system doesn't provide a secure random generator!"))
        return False

    # Generate a secure random password for Guest Accounts
    random_password = "".join(r.choice(letters) for _ in range(6))

    for uw in undesireable_words:
        if uw in random_password.lower():
            print("[!] Detected undesirable word in password, generating a new one!")
            # I assume our chances are very low to generate two undesireable words in a row
            random_password = "".join(r.choice(letters) for _ in range(6))
            break

    guest_data = {
        "creator":settings['guest_operator_username'],
        "accountType":"Account",
        "password":random_password,
        "repeat":random_password,
        "username":guest_name,
        "dataQuotaAmount":1000,
        "accountValidityPeriod":valid_until * 1000,
        "dataQuota":"Disabled",
        "description":f"OmniPortal - Add Guest by {g.user}"
    }

    resp_guest = req.post(f"{settings['guest_operator_url']}/sponsor/api/ham/guest/account/addAccount", json=guest_data)
    print("Accounts: ", resp_guest.status_code, resp_guest.reason)
    print(json.dumps(resp_guest.json(), indent=4))
    req.get(f"{settings['guest_operator_url']}/sponsor/api/ham/guest/manager/logout")
    if resp_guest.json()['errorCode'] != 0:
        if resp_guest.json()['errorMessage'] == "upam.accountNameRepeat":
            flash(_('An account with this username already exists!'))
            return False
    send_ms_teams_card(guest_name, random_password, datetime.datetime.fromtimestamp(valid_until).strftime("%d.%m.%Y, %H:%M:%S"))
    send_ringcentral_card(guest_name, random_password, datetime.datetime.fromtimestamp(valid_until).strftime("%d.%m.%Y, %H:%M:%S"))
    send_rainbow_card(guest_name, random_password, datetime.datetime.fromtimestamp(valid_until).strftime("%d.%m.%Y, %H:%M:%S"))
    flash(_('The guest account was created!'), 'success')

def send_rainbow_card(guest_name, password, valid_until):
    # Pass all translateable text via this function, card is defined in VNA
    settings = read_settings()

    webhook_header = {
        "Content-Type": "application/json",
    }

    if settings['ale_rainbow_webhook'] == "":
        return False

    guest_card = {}
    guest_card["title_lbl"] = _('Guest Access to Stellar Wireless')
    guest_card["wifi_network_lbl"] = _('Wi-Fi Network:')
    guest_card["username_lbl"] = _('Username:')
    guest_card["password_lbl"] = _('Password:')
    guest_card["valid_lbl"] = _('Access valid until:')
    guest_card["contact_lbl"] = _('Your contact person:')
    guest_card["guest_username"] = guest_name
    guest_card["guest_password"] = password
    guest_card["valid_until"] = valid_until
    guest_card["contact"] = g.user.capitalize()
    guest_card["wifi_network"] = settings['wifi_network']
    print(guest_card)

    webhook_resp = requests.post(settings['ale_rainbow_webhook'], headers=webhook_header, json=guest_card)

    if webhook_resp.status_code == 200 or webhook_resp.status_code == 201:
        print(webhook_resp.status_code, webhook_resp.reason, "- Message delivered to ALE VNA")
        print(json.dumps(webhook_resp.json(), indent=4))
    else:
        flash(_('Failed to deliver to ALE VNA!'))
        return False

def send_ringcentral_card(guest_name, password, valid_until):
    settings = read_settings()

    card_msg = {
        "activity": "Alcatel-Lucent Enterprise",
        "iconUri": "https://bennye.github.io/logos/logo-rgb.png",
        "attachments": [
                      {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "type": "AdaptiveCard",
    "version": "1.3",
    "body": [
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "Image",
                            "url": "https://bennye.github.io/logos/al_enterprise_bk_50mm.png",
                            "height": "60px",
                            "horizontalAlignment": "Left"
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "Image",
                            "url": "https://bennye.github.io/logos/stellar-logo.png",
                            "height": "60px",
                            "horizontalAlignment": "Right"
                        }
                    ]
                }
            ]
        },
        {
            "type": "TextBlock",
            "text": _("Guest Access to Stellar Wireless"),
            "weight": "Bolder",
            "size": "Medium",
            "wrap": True
        },
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "Image",
                            "url": "https://openrainbow.com/api/channel-avatar/5c6c3c236f89d92902c3a845",
                            "size": "Small",
                            "height": "90px"
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "400px",
                    "items": [
                        {
                            "type": "FactSet",
                            "facts": [
                                {
                                    "title": _("Wi-Fi Network:"),
                                    "value": settings['wifi_network']
                                },
                                {
                                    "title": _("Username:"),
                                    "value": guest_name
                                },
                                {
                                    "title": _("Password:"),
                                    "value": password
                                },                             
                                {
                                    "title": _("Access valid until:"),
                                    "value": valid_until
                                },
                                {
                                    "title": _("Your contact person:"),
                                    "value": g.user.capitalize()
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        ]
    }
        ]
    }

    if settings['ringcentral_webhook'] == "":
        return False
    webhook_header = {
        "Content-Type": "application/json"
    }
    webhook_card_resp = requests.post(settings['ringcentral_webhook'], headers=webhook_header, json=card_msg)

    if webhook_card_resp.status_code == 200 or webhook_card_resp.status_code == 201:
        print(webhook_card_resp.status_code, webhook_card_resp.reason, "- Webhook/App/Post/Card")
        print(json.dumps(webhook_card_resp.json(), indent=4))
    else:
        flash(_l('Sending card via RingCentral webhook failed!'), 'danger')
    


def send_ms_teams_card(guest_name, password, valid_until):
    settings = read_settings()

    msteamscard =  {
    "type":"message",
    "attachments":[
       {
          "contentType":"application/vnd.microsoft.card.adaptive",
          "contentUrl": None,
          "content":
          {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "type": "AdaptiveCard",
    "version": "1.4",
    "msteams": {
        "width": "Full"
    },
    "body": [
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "Image",
                            "url": "https://bennye.github.io/logos/al_enterprise_bk_50mm.png",
                            "height": "60px",
                            "horizontalAlignment": "Left"
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "Image",
                            "url": "https://bennye.github.io/logos/stellar-logo.png",
                            "height": "60px",
                            "horizontalAlignment": "Right"
                        }
                    ]
                }
            ]
        },
        {
            "type": "TextBlock",
            "text": _("Guest Access to Stellar Wireless"),
            "weight": "Bolder",
            "size": "Medium",
            "wrap": True
        },
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "Image",
                            "url": "https://openrainbow.com/api/channel-avatar/5c6c3c236f89d92902c3a845",
                            "size": "Small",
                            "height": "90px"
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "400px",
                    "items": [
                        {
                            "type": "FactSet",
                            "facts": [
                                {
                                    "title": _("Wi-Fi Network:"),
                                    "value": settings['wifi_network']
                                },
                                {
                                    "title": _("Username:"),
                                    "value": guest_name
                                },
                                {
                                    "title": _("Password:"),
                                    "value": password
                                },                             
                                {
                                    "title": _("Access valid until:"),
                                    "value": valid_until
                                },
                                {
                                    "title": _("Your contact person:"),
                                    "value": g.user.capitalize()
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        ]
    }
       }
        ]
    }
    if settings['ms_teams_webhook'] == "":
        return False
    webhook_header = {
        "Content-Type": "application/json"
    }
    webhook_card_resp = requests.post(settings['ms_teams_webhook'], headers=webhook_header, json=msteamscard)

    print(webhook_card_resp.status_code, webhook_card_resp.reason, webhook_card_resp.text)
    print(json.dumps(webhook_card_resp.json(), indent=4))

@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    return datetime.datetime.strftime(datetime.datetime.fromtimestamp(timestamp/1000), "%d.%m.%Y %H:%M")

@app.route("/guest_accounts")
#@login_required
@guest_required
def guest_accounts():

    guest_accounts = get_guest_accounts()
    guest_data = guest_accounts['data']

    titles = [
        ('username', _('Username')),
        ('dateOfEffective', _('Valid From')),
        ('accountValidityPeriod', _('Valid Until')),
        ('actions', _('Actions'))
    ]

    return render_template("guest_accounts.html", data=guest_data, titles=titles)

@app.route('/guest_accounts/<int:guest_id>/view')
def view_message(guest_id):
    message = guest_id
    if message:
        return f'Viewing {guest_id} with text "{guest_id}". Return to <a href="/guest_accounts">table</a>.'
    return f'Could not view message {guest_id} as it does not exist. Return to <a href="/guest_accounts">table</a>.'

@app.route("/add_guest", methods=["POST", "GET"])
#@login_required
@guest_required
def add_guest():
    form=AddGuestForm()
    quick_guest=QuickGuestForm()
    if request.method == "POST":
        # Check if the QuickGuest function was used
        if request.form.get('one_day'):
            quick_guest_account(1)
        elif request.form.get('three_days'):
            quick_guest_account(3)
        elif request.form.get('five_days'):
            quick_guest_account(5)
        elif request.form.get('seven_days'):
            quick_guest_account(7)
        elif request.form.get('fourteen_days'):
            quick_guest_account(14)
        elif request.form.get('thirty_days'):
            quick_guest_account(30)
        print(request.form)

        if request.form.get('username') and request.form.get('valid_until'):
            print(request.form.get('username'))
            print(request.form.get('valid_until'))
            if not form.validate_on_submit():
                return render_template("add_guest.html", form=form, quick_guest=quick_guest)
            # TODO: check if this is in the past
            if request.form.get('valid_until') == datetime.datetime.now().strftime("%Y-%m-%d"):
                # Assume that the account should be valid today, so we make it valid until tomorrow
                new_date = datetime.datetime.now()
                valid_until = int(time.mktime(datetime.datetime.strptime(f"{new_date.strftime('%Y-%m-')}{int(new_date.strftime('%d'))+1}", "%Y-%m-%d").timetuple()))
            else:
                valid_until = int(time.mktime(datetime.datetime.strptime(request.form.get('valid_until'), "%Y-%m-%d").timetuple()))
            create_guest_account(request.form.get('username'), valid_until)
            return redirect(url_for('add_guest'))
    return render_template("add_guest.html", form=form, quick_guest=quick_guest)

@app.route("/test_guest", methods=["POST", "GET"])
#@login_required
@guest_required
def test_guest():
    form=TestGuestForm()
    if not form.validate_on_submit():
        print(form.data)
        return render_template("test_guest.html", form=form)
    else:
        print("SUCCESS!")
    return render_template("test_guest.html", form=form)

@app.route("/employee_accounts")
#@login_required
@employee_required
def employee_accounts():
    employee_accounts = get_employee_accounts()
    employee_data = employee_accounts['data']
    print(employee_data)
    # >>> request.host
    # 'omniportal2-127.0.0.1.sslip.io:5001'
    titles = [
        ('username', _('Username')),
        ('email', _('Email')),
        ('telephone', _('Telephone (Mobile)')),
        ('status', _('Status')),
        ('dateOfEffective', _('Valid From')),
        ('actions', _('Actions'))
    ]
    return render_template("employee_accounts.html", data=employee_data, titles=titles)

@app.route("/add_employee", methods=["POST", "GET"])
#@login_required
@employee_required
def add_employee():
    form=AddEmployeeForm()
    if request.method == "POST":
        print(request.form)
        if request.form.get('username') and request.form.get('email') and request.form.get('telephone'):
            print(request.form.get('username'))
            print(request.form.get('email'))
            print(request.form.get('telephone'))
            if not form.validate_on_submit():
                return render_template("add_employee.html", form=form)
            create_employee_account(request.form.get('username'), request.form.get('email'), request.form.get('telephone'))
            return redirect(url_for('add_employee'))
    return render_template("add_employee.html", form=form)