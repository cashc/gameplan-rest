from flask_app import app, db, oauth
from flask_app.models import *
from flask import redirect, request, render_template, session, jsonify
from werkzeug.security import gen_salt
from datetime import datetime, timedelta
import random
import string
from hashlib import sha512

SIMPLE_CHARS = string.ascii_letters + string.digits

@app.route('/client')
def client():
    user = current_user()
    if not user:
        return redirect('/')
    if request.user_agent.platform:
        client_name = request.user_agent.platform + " " + request.user_agent.browser
    else:
        client_name = 'postman'
    item = Client(gen_salt(40), gen_salt(50), client_name, user.id, False,
                  ' '.join([
                      'http://localhost:5000/authorized',
                      'http://127.0.0.1:5000/authorized',
                      'https://www.getpostman.com/oauth2/callback',
                  ]), 'A'
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(
        client_id=item.client_id,
        client_secret=item.secret,
    )

@app.route('/oauth/authorize', methods=['GET', 'POST'])
@oauth.authorize_handler
def authorize(*args, **kwargs):
    user = current_user()
    if not user:
        return redirect('/')
    if request.method == 'GET':
        client_id = kwargs.get('client_id')
        client = db.session.query(Client).get(client_id)
        kwargs['client'] = client
        kwargs['user'] = user
        return render_template('authorize.html', **kwargs)

    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'


@app.route('/oauth/token', methods=['POST'])
@oauth.token_handler
def access_token():
    return None

@app.route('/oauth/revoke', methods=['POST'])
@oauth.revoke_handler
def revoke_token(): pass


@oauth.clientgetter
def load_client(id):
    return db.session.query(Client).get(id)


@oauth.grantgetter
def load_grant(client_id, code):
    return db.session.query(Grant).filter_by(client_id=client_id, code=code).first()


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    print("save_grant")
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(None, current_user().id, client_id, code['code'], request.redirect_uri, expires, ' '.join(request.scopes))
    db.session.add(grant)
    db.session.commit()
    return grant


@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        return db.session.query(Token).filter_by(access_token=access_token).first()
    elif refresh_token:
        return db.session.query(Token).filter_by(refresh_token=refresh_token).first()


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    toks = db.session.query(Token).filter_by(client_id=request.client.client_id,
                                 user=request.user)
    # make sure that every client has only one token connected to a user
    for t in toks:
        db.session.delete(t)
    #pprint.pprint(token)
    expiresin = token['expires_in']
    expires = datetime.utcnow() + timedelta(seconds=expiresin)

    tok = Token(None, request.client.client_id, request.user, token['token_type'], token['access_token'],
                token['refresh_token'], expires, token['scope'])
    db.session.add(tok)
    db.session.commit()
    return tok

@oauth.usergetter
def get_user(username, password, *args, **kwargs):
    user = db.session.query(Users).filter_by(username=username).first()
    #if user.check_password(password):
        #return user
    return user

def current_user():
    if 'id' in session:
        uid = session['id']
        return db.session.query(Users).get(uid)
    return None

def randomString(length=32):
    return ''.join(random.choice(SIMPLE_CHARS) for i in range(length))

def randomHash(length=32):
    hash = sha512()
    hash.update(randomString())
    return hash.hexdigest()[:length]