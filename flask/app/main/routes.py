from flask import Blueprint, render_template, url_for, flash, redirect, Response, session
from app.main.forms import LoginForm, ScrapeForm
from app.main.mail import ScrapeEmails, validate_email

main = Blueprint('main', __name__)


@main.route("/home", methods=['GET', 'POST'])
def home():
    form = ScrapeForm()
    # if payment email sender and target date ar valid, save info in session and proceed to download a csv list
    if form.validate_on_submit():
        session["email_folder"] = form.email_folder.data
        session["date"] = form.date.data
        return redirect(url_for('main.downloadCSV'))
    return render_template('home.html', title='Home', form=form)


@main.route("/downloadCSV")
def downloadCSV():
    # collect data from session and scrape client emails
    userEmail = session.get("email", None)
    userPass = session.get("pass", None)
    emailFolder = session.get("email_folder", None)
    stopDate = session.get("date", None)
    s = ScrapeEmails(emailFolder, stopDate)
    firstNameList, lastNameList, emailList = s.mail_list(userEmail, userPass)
    # if at least one client email was scraped, convert list to csv and download, otherwise advise user that no
    # client emails were found.
    if len(emailList) > 1:
        csv = ''
        for first_name, last_name, email in zip(firstNameList, lastNameList, emailList):
            csv = csv + first_name + ',' + last_name + ',' + email + '\n'
        return Response(
            csv,
            mimetype="text/csv",
            headers={"Content-disposition":
                         "attachment; filename=email_list.csv"})
    elif len(emailList) == 1:
        flash(f'There are no emails from in the folder {emailFolder} for the specified time frame.', 'danger')
        return redirect(url_for('main.home'))
    else:
        flash(f'The folder {emailFolder} does not exist in {userEmail}.', 'danger')
        return redirect(url_for('main.home'))

@main.route("/", methods=['GET', 'POST'])
@main.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    # if user email and password are valid, save info in session and direct to download/scraping home page
    if form.validate_on_submit():
        mail = validate_email(form.email.data, form.password.data)
        if mail:
            session["email"] = form.email.data
            session["pass"] = form.password.data
            flash('You have been logged in!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)
