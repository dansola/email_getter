import imaplib
from dateutil import parser
import email
import re
import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor


# break buyer name into first and last
def split_name(name):
    first_name_ind = name.find(' ')
    return name[:first_name_ind], name[first_name_ind + 1:]


# get email address from string
def get_email(string):
    match = re.search(r'[\w\.-]+@[\w\.-]+', string)
    return match.group(0)


# get buyer info as structured in hotmail email
def get_buyer_hotmail(buyer_string, search_string='<span style="display:inline;">'):
    first_ind = buyer_string.find(search_string)
    second_ind = buyer_string[first_ind + len(search_string):].find('<')
    name = buyer_string[first_ind + len(search_string):first_ind + len(search_string) + second_ind].replace('\n',
                                                                                                            '')
    first_name, last_name = split_name(name)
    emailAddress = get_email(buyer_string)
    return first_name, last_name, emailAddress


# get buyer info as structured in gmail email
def get_buyer_gmail(buyer_string):
    first_ind = buyer_string.find('\n')
    second_ind = buyer_string[first_ind:].find('\r')
    name = buyer_string[first_ind + 1:first_ind + second_ind]  # extract name
    name = name.replace('> ', '')
    if name[0] == ' ':
        name = name[1:]
    first_name, last_name = split_name(name)
    emailAddress = get_email(buyer_string)
    return first_name, last_name, emailAddress


# parse the body of the email
def get_body(b):
    body = ""
    if b.is_multipart():
        for part in b.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                body = part.get_payload(decode=True)  # decode
                break
    else:
        body = b.get_payload(decode=True)
    return body.decode("utf-8")


# from the body of the email extract the name and email address of the buyer
def get_name_email(body, template=1):
    # find part of email content that has buyer name and email
    first_ind = body.find('Buyer')
    second_ind = body[first_ind:].find('mailto')
    if second_ind == -1:
        second_ind = body[first_ind:].find('Instructions')
    buyer_string = body[first_ind:first_ind + second_ind]  # string that has buyer name and email
    if template == 0:
        first_name, last_name, emailAddress = get_buyer_gmail(buyer_string)
        # first_name, last_name, emailAddress = get_buyer_hotmail(buyer_string, search_string='<span>')
    else:
        first_name, last_name, emailAddress = get_buyer_gmail(buyer_string)
        # first_name, last_name, emailAddress = get_buyer_hotmail(buyer_string)

    return first_name, last_name, emailAddress


# given the email information, collect client emails
class ScrapeEmails:
    def __init__(self, email_folder, date):
        """
        :param email_sender:    Email address which sends the user the client payent information. e.g. PayPal email.
        :type email_sender:     str
        :param date:            Latest date to for the algorithm will gather client emails (format %m/%d/%Y).
        :type date:             str
        """
        self.email_folder = email_folder
        self.finalDate = parser.parse(date)
        self.firstNameList = ['First Name'] # email list header
        self.lastNameList = ['Last Name']   # email list header
        self.emailList = ['Email']          # email list header
        self.emailDate_dt = datetime.datetime(2222, 2, 22, 0, 0).replace(
            tzinfo=pytz.UTC)  # individual email sent date initialized in the future
        self.mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)  # gmail
        # self.mail = imaplib.IMAP4_SSL("imap-mail.outlook.com", 993)  # outlook/hotmail
        # self.mail = imaplib.IMAP4_SSL("imap.secureserver.net", 993) # godaddy
        # self.mail = imaplib.IMAP4_SSL("outlook.office365.com", 993) # office 365

    def mail_list(self, email_user, email_pass):
        """
        :param email_user:  User email address to which client emails are sent to.
        :type email_user:   str
        :param email_pass:  User email password to above email address.
        :type email_pass:   str
        :return:            List of client email addresses.
        :rtype:             list
        """
        self.mail.login(email_user, email_pass)
        # print('"' + self.email_folder + '"')
        rv, data = self.mail.select('"' + self.email_folder + '"')
        # print(rv)
        #rv, data = self.mail.select(self.email_folder)
        if rv == 'OK':
            rv, data = self.mail.search(None, "ALL")
            nums = [x for x in reversed(data[0].split())]  # reverse email order to start with most recent
            i = 0

            # while individual email dates are more recent than user input, scrape emails using threads
            with ThreadPoolExecutor() as executor:
                while self.emailDate_dt > self.finalDate.replace(tzinfo=pytz.UTC):
                    if len(nums) == i:
                        break
                    executor.submit(self.get_email, nums[i]).result()
                    i += 1
            return self.firstNameList, self.lastNameList, self.emailList
        else:
            return [], [], []

    def get_email(self, num):
        """
        :param num: Email number in user inbox.
        :type num:  str
        """
        rv, data2 = self.mail.fetch(num, '(RFC822)')
        email_content = data2[0][1]  # individual email in bytes
        msg = email.message_from_bytes(email_content)  # convert email to string
        emailDate = msg["Date"]  # date email was sent
        emailDate = emailDate.replace(' (UTC)', '')
        # try updating date at which the email was sent, occasionally email will not have a date, or it will have a
        # weird format.  I found that this was very rare.
        try:
            date_temp = datetime.datetime.strptime(emailDate, "%a, %d %b %Y %H:%M:%S %z")
        except:
            date_temp = self.emailDate_dt

        if date_temp >= self.finalDate.replace(tzinfo=pytz.UTC):
            self.emailDate_dt = date_temp
            emailSubject = msg["Subject"]  # email subject
            body = get_body(msg)
            if body:
                # test if sender and subject criteria match email, if they do, add client email to list.
                if "payment received from" in emailSubject.lower() and 'Buyer' in body:
                    first_name, last_name, emailAddress = get_name_email(body, template=0)
                    if emailAddress not in self.emailList:
                        if 'n>' in first_name:
                            first_name.replace('n>', '')
                        self.firstNameList.append(first_name)
                        self.lastNameList.append(last_name)
                        self.emailList.append(emailAddress)

                elif 'notification of payment received' in emailSubject.lower() and 'Buyer' in body:
                    first_name, last_name, emailAddress = get_name_email(body)
                    if emailAddress not in self.emailList:
                        if 'n>' in first_name:
                            first_name.replace('n>', '')
                        self.firstNameList.append(first_name)
                        self.lastNameList.append(last_name)
                        self.emailList.append(emailAddress)
        else:
            self.emailDate_dt = datetime.datetime(1996, 12, 29, 0, 0).replace(
                tzinfo=pytz.UTC)


# check if login credentials are valid
def validate_email(email_user, email_pass):
    """
    :param email_user:  User email address to which client emails are sent to.
    :type email_user:   str
    :param email_pass:  User email password to above email address.
    :type email_pass:   str
    :return:            Whether or not the email was valid given the imap address.
    :rtype:             bool
    """
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)  # gmail
    # mail = imaplib.IMAP4_SSL("outlook.office365.com", 993) # office 365
    # mail = imaplib.IMAP4_SSL("imap.secureserver.net", 993) # godaddy
    # mail = imaplib.IMAP4_SSL("imap-mail.outlook.com", 993)  # outlook/hotmail
    try:
        rv, data = mail.login(email_user, email_pass)
        if rv == 'OK':
            return True
        else:
            return False
    except:
        return False
