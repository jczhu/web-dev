import os
import re

import jinja2
import webapp2

from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))


class Entry(db.Model):
	title = db.StringProperty(required = True)
	entry = db.TextProperty(required = True)
	created = db.DateProperty(auto_now_add = True)

class MainPage(Handler):
	def get(self):
		entries = db.GqlQuery("SELECT * FROM Entry ORDER BY created DESC")

		self.render("front.html", entries = entries)

class NewPost(Handler):
	def render_newpost(self, title="", entry="", error=""):
		self.render("newpost.html", title=title, entry=entry, error=error)

	def get(self):
		self.render_newpost()

	def post(self):
		title = self.request.get("title")
		entry = self.request.get("entry")

		if title and entry:
			e = Entry(title = title, entry = entry)
			e.put()

			self.redirect("/"+str(e.key().id()))
		else:
			error = "we need both a title and a blog entry"
			self.render_newpost(title, entry, error)

class BlogPost(Handler):
	def get(self, entry_id):
		e = Entry.get_by_id(int(entry_id))
		self.render("single-entry.html", entry=e)

class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty()

class SignUp(Handler):
    def render_form(self, username="", invalid_user="", invalid_pass="", diff_pass="", 
        invalid_email=""):
        self.render("signup.html", username=username, invalid_user=invalid_user,
        	invalid_pass=invalid_pass, diff_pass=diff_pass, invalid_email=invalid_email)

    def get(self):
        self.render_form()

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        check_username = valid_username(username)
        check_password = valid_password(password)
        check_verify = (password == verify)
        check_email = valid_email(email)

        user_error, pass_error, verify_error, email_error = "", "", "", ""
        if not check_username: # also check if username already in database
            user_error = "That's not a valid username."
        if not check_password:
            pass_error = "That's wasn't a valid password."
        if not check_verify:
            verify_error = "Your passwords didn't match."
        if not check_email:
            email_error = "That's not a valid email."

        if check_username and check_password and check_verify and check_email:
            self.redirect("/welcome?username=" + username) #this will have to change, store username w/cookie
        else:
            self.render_form(username, user_error, pass_error, verify_error, email_error)

class Welcome(Handler):
    def get(self):
        self.response.out.write("Welcome, " + self.request.get('username') + "!")

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def valid_username(username):
    return USER_RE.match(username)

def valid_password(password):
    return PASS_RE.match(password)

def valid_email(email):
    return EMAIL_RE.match(email) or email == ''

app = webapp2.WSGIApplication([
    ('/', MainPage), ('/newpost', NewPost), (r'/(\d+)', BlogPost), ('/signup', SignUp), 
    ('/welcome', Welcome)
], debug=True)