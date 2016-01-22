import webapp2
import cgi
import re

form = """
<html>
  <head>
    <title>Sign Up</title>
    <style type="text/css">
      .label {text-align: right}
      .error {color: red}
    </style>

  </head>

  <body>
    <h2>Signup</h2>
    <form method="post">
      <table>
        <tr>
          <td class="label">
            Username
          </td>
          <td>
            <input type="text" name="username" value="%(username)s">
          </td>
          <td class="error">
            %(invalid_user)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Password
          </td>
          <td>
            <input type="password" name="password" value="">
          </td>
          <td class="error">
            %(invalid_pass)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Verify Password
          </td>
          <td>
            <input type="password" name="verify" value="">
          </td>
          <td class="error">
            %(diff_pass)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Email (optional)
          </td>
          <td>
            <input type="text" name="email" value="">
          </td>
          <td class="error">
            %(invalid_email)s
          </td>
        </tr>
      </table>

      <input type="submit">
    </form>
  </body>

</html>
"""

class MainPage(webapp2.RequestHandler):
    def write_form(self, username="", invalid_user="", invalid_pass="", diff_pass="", 
        invalid_email=""):
        self.response.out.write(form%{"username": escape_html(username),
                                        "invalid_user": escape_html(invalid_user),
                                        "invalid_pass": escape_html(invalid_pass),
                                        "diff_pass": escape_html(diff_pass),
                                        "invalid_email": escape_html(invalid_email)})

    def get(self):
        self.write_form()

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
        if not check_username:
            user_error = "That's not a valid username."
        if not check_password:
            pass_error = "That's wasn't a valid password."
        if not check_verify:
            verify_error = "Your passwords didn't match."
        if not check_email:
            email_error = "That's not a valid email."

        if check_username and check_password and check_verify and check_email:
            self.redirect("/welcome?username=" + username)
        else:
            self.write_form(username, user_error, pass_error, verify_error, email_error)

class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Welcome, " + self.request.get('username') + "!")

def escape_html(s):
    return cgi.escape(s, quote = True)

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
    ('/', MainPage), ('/welcome', WelcomeHandler)
], debug=True)