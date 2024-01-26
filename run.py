from flask import Flask, render_template
import os

app = Flask(__name__)


@app.route("/")
def show_index():
	return render_template("index.html")

@app.route("/favicon.ico")
def show_fav():
	return ""

@app.route("/<filename>")
def show_file(filename):
	return render_template(filename)


def main():
	app.debug = True
	# app.run(host=os.getenv('APP_ADDRESS', 'localhost'), port=8000)
	app.run(host='0.0.0.0', port=8000)
  
if __name__ == '__main__':
	main()
