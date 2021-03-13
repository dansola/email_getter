# Email_Getter

## Purpose of App
During the Covid-19 pandemic, a family friend moved her previously in-person art and photography classes online.  She started to collect payments via PayPal and wanted to assemble a simple list of her clients in an excel spread sheet.  To do this, she went through her emails one by one, looking for the "PayPal payment received" email she got from PayPal. From here she copy and pasted her client's email address into a spreadsheet.  This manual process took hours of her time every month.  Knowing a bit of Python, I figured I could automate this process for her. This led me to make Email_Getter; a small web app that scrapes client email addresses from your email account.

## How it Works
**Email Scraping:** I used the [imaplib](https://docs.python.org/2/library/imaplib.html) to allow the user to log into their email account.  This requires the IMAP server and port for the given account provider (e.g. imap.gmail.com and port 993 for Gmail) and connects over an SSL encrypted socket.  From here I can access the user’s emails from specific email folders as requested by the end user.  The algorithm then identifies PayPal emails based on certain key phrases contained in PayPal's email templates.  Depending on the template, the client email address is either specified in the subject line or return address.  This address can then be appended to a list and eventually exportd to a CSV upon the users request in the web app.  Given the large number of I/O operations required to read the emails, this process was threaded using [concurrent.features](https://docs.python.org/3/library/concurrent.futures.html).

**Flask App:** The [Flask](https://flask.palletsprojects.com/en/1.1.x/) application is quite simple and only consists of two pages; a login page and a home page.  The user logs in given their email address and password for the email address they want to scrape from (the email to which the PayPal emails are sent to).  If the credentials are correct you are taken to the home page which gives you a couple of options before you scrape the client email addresses.  You are able to specify the email folder for which the user wishes to search, and how far back in time you want to scrape.  My family friend has been adding client emails to her list every month, so she might want to specify the last time she ran the algorithm before scraping as to not re-append emails to the list.  Both the login page and home page are created using [WTForms](https://wtforms.readthedocs.io/en/2.3.x/), while [bootstrap](https://getbootstrap.com/) was used for some design features.  Invalid email addreses, email folders, and dates entered by the user are adderessed with a message idtentifying the issue and suggesting a fix (e.g. "Please check your email and password.").

**Deployment:** For this app, [NGINX](https://www.nginx.com/) is used as a web server which serves static content to the user, reverse proxies requests to an upstream server, and provides load balancing. [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) is used to handle http requests from NGINX and routes them to Flask.  The Flask app and NGINX server are containerized using [Docker](https://www.docker.com/) which allows for operating system level virtualization.  This lets someone run the application from anywhere using any computer as long as they have docker; removing any concern for dependencies, deprecation, etc.  Finally, the docker containers were run on [GCP (Google Cloud Platform)](https://cloud.google.com/) using a free f1-micro instance so the application can be used anywhere in the world.

## How to Run
Right now GCP VM might not be running.  If you wish to play around with the web app there a few simple steps you need to follow. First make sure you have [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) installed using these links.  Next, all you need to do is clone this repo, `cd` into the repo, run the shell command `docker-compose up --build` and visit [http://localhost/](http://localhost/) in your browser.

## Resources I Used
**Building the Flask App:** The [Flask Tutorial Series by Corey Schafer](https://www.youtube.com/playlist?list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH) is very helpful and is also where I got the CSS and HTML templates that I built off of.

**Deployment Frameworks:** Check out these blog posts by [Patrick Kennedy](https://www.patricksoftwareblog.com/how-to-configure-nginx-for-a-flask-web-application/) and [Julian Nash](https://pythonise.com/series/learning-flask/building-a-flask-app-with-docker-compose) for information on things like NGINX, uWSGI, Gunicorn, Flask, and Docker.

**Cloud Hosting:** The [GCP Documentation](https://cloud.google.com/compute/all-pricing) was pretty helpful, especially with regards to keeping this project free.

**Email Scraping:** A lot of stackoverflow searches.

## Page Examples
![alt text](https://github.com/dansola/Email_Getter/blob/master/images/login.png)
![alt text](https://github.com/dansola/Email_Getter/blob/master/images/home.png)
