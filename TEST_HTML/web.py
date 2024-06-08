from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route('/para/<user>')
def index(user):
    return render_template('abc.html', user_template=user)

if __name__ == '__main__':
    app.debug = True
    app.run()