import webapp2
import cgi

form = """
<html>
  <head>
    <title>Unit 2 Rot 13</title>
  </head>

  <body>
    <h2>Enter some text to ROT13:</h2>
    <form method="post">
      <textarea name="text"
                style="height: 100px; width: 400px;"
                >%s</textarea>
      <br>
      <input type="submit">
    </form>
  </body>

</html>
"""

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(form%'')

    def post(self):
        encode = self.request.get('text')
        encode = rot(encode)
        encode = escape_html(encode)
        self.response.out.write(form%encode)


def escape_html(s):
    return cgi.escape(s, quote = True)

def rot(s):
    result = ''
    for c in s:
        if c == '\n':
            result = result + '\n'
        elif c.isupper():
            shifted = (ord(c) - ord('A') + 13) % 26
            result += chr(ord('A') + shifted)
        elif c.islower(): # c is lowercase
            shifted = (ord(c) - ord('a') + 13) % 26
            result += chr(ord('a') + shifted)
        else:
            result += c
    return result


app = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)