import http.server
import socketserver

import os
import urllib.parse
import email.utils
import datetime
from http import HTTPStatus

CHECK_MODIFY = False
PORT = 8000

class MyHandler(http.server.SimpleHTTPRequestHandler):
  def my_send_head(self):
      path = self.translate_path(self.path)
      f = None
      if os.path.isdir(path):
          parts = urllib.parse.urlsplit(self.path)
          if not parts.path.endswith('/'):
              # redirect browser - doing basically what apache does
              self.send_response(HTTPStatus.MOVED_PERMANENTLY)
              new_parts = (parts[0], parts[1], parts[2] + '/',
                            parts[3], parts[4])
              new_url = urllib.parse.urlunsplit(new_parts)
              self.send_header("Location", new_url)
              self.send_header("Content-Length", "0")
              self.end_headers()
              return None
          for index in "index.html", "index.htm":
              index = os.path.join(path, index)
              if os.path.exists(index):
                  path = index
                  break
          else:
              return self.list_directory(path)
      ctype = self.guess_type(path)
      # check for trailing "/" which should return 404. See Issue17324
      # The test for this was added in test_httpserver.py
      # However, some OS platforms accept a trailingSlash as a filename
      # See discussion on python-dev and Issue34711 regarding
      # parseing and rejection of filenames with a trailing slash
      if path.endswith("/"):
          self.send_error(HTTPStatus.NOT_FOUND, "File not found")
          return None
      try:
          f = open(path, 'rb')
      except OSError:
          self.send_error(HTTPStatus.NOT_FOUND, "File not found")
          return None

      try:
          fs = os.fstat(f.fileno())
          # Use browser cache if possible
          if ("If-Modified-Since" in self.headers
                  and "If-None-Match" not in self.headers):
              # compare If-Modified-Since and time of last file modification
              try:
                  ims = email.utils.parsedate_to_datetime(
                      self.headers["If-Modified-Since"])
              except (TypeError, IndexError, OverflowError, ValueError):
                  # ignore ill-formed values
                  pass
              else:
                  if ims.tzinfo is None:
                      # obsolete format with no timezone, cf.
                      # https://tools.ietf.org/html/rfc7231#section-7.1.1.1
                      ims = ims.replace(tzinfo=datetime.timezone.utc)
                  if CHECK_MODIFY and ims.tzinfo is datetime.timezone.utc:
                      # compare to UTC datetime of last modification
                      last_modif = datetime.datetime.fromtimestamp(
                          fs.st_mtime, datetime.timezone.utc)
                      # remove microseconds, like in If-Modified-Since
                      last_modif = last_modif.replace(microsecond=0)
                      if last_modif <= ims:
                          self.send_response(HTTPStatus.NOT_MODIFIED)
                          self.end_headers()
                          f.close()
                          return None

          self.send_response(HTTPStatus.OK)
          self.send_header("Content-type", ctype)
          self.send_header("Content-Length", str(fs[6]))
          self.send_header("Last-Modified",
              self.date_time_string(fs.st_mtime))
          self.send_header('Content-type', 'text/html; charset=utf-8')
          self.end_headers()
          return f
      except:
          f.close()
          raise

  def do_GET(self):
    f = self.my_send_head()
    if f:
      try:
        self.copyfile(f, self.wfile)
      finally:
        f.close()

  def do_POST(self):
    f = self.my_send_head()
    if f:
      try:
        self.copyfile(f, self.wfile)
      finally:
        f.close()
    

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
  print("server at port", PORT)
  httpd.serve_forever()
  