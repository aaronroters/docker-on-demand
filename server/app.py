from flask import Flask, request, jsonify
from functools import wraps
import requests
import jwt
import sys
import threading
import os
import logging
import random
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from sqlalchemy import text
from datetime import datetime
from deployer import *

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
logging.basicConfig(filename='debug.log', level=logging.WARNING, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

class Deployment(db.Model):
    deployment_id = db.Column(db.String(65), primary_key=True)
    user_id = db.Column(db.String(200), nullable=False)
    challenge_id = db.Column(db.String(200), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    
    def __init__(self, deployment_id, user_id, challenge_id, port):
        self.deployment_id = deployment_id
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.port = port

def jwt_verification(params):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try: 
                body = request.get_json()["body"]
                payload = jwt.decode(body, SECRET, algorithms=["HS256"])
                missing = [r for r in params if r not in payload]
                if missing:
                    raise ValueError("Required params not supplied.")
            except:
                response = {'status': 'fail', 'message': 'Invalid token supplied.'}
                return jsonify(response), 400
            return fn(* tuple(payload[item] for item in params))
        return wrapper
    return decorator

def auto_clear():
    current_timestamp = datetime.utcnow()
    sql = text('SELECT deployment_id FROM Deployment WHERE ROUND((JULIANDAY(created_at) - JULIANDAY(current_timestamp)) * 1440) > :expiry').bindparams(expiry=expiry)
    expired_deployments = db.session.execute(sql).all()
    for deployment in expired_deployments:
        remove_deployment(deployment[0])
    db.session.commit()
    threading.Timer(60, auto_clear).start()

def remove_deployment(deployment_id):
    kill(deployment_id)
    Deployment.query.filter_by(deployment_id=deployment_id).delete()
    db.session.commit()

@app.errorhandler(Exception)
def server_error(err):
    app.logger.exception(err)
    return jsonify({'status': 'fail'})  

@app.route('/get_deployments', methods=['POST'])
@jwt_verification(["user_id"])
def get_deployments(user_id):
    deployment = Deployment.query.filter_by(user_id=user_id).first()
    if deployment is None:
        return jsonify({'status': 'fail', 'message': 'No deployments found.'}), 404
    else:
        return jsonify({'status': 'success', 'url': f"{HOST_IP}:{deployment.port}/"})  
    
@app.route('/deploy', methods=['POST'])
@jwt_verification(["challenge_id", "user_id"])
def deploy_challenge(challenge_id, user_id):   
    deployment = Deployment.query.filter_by(user_id=user_id, challenge_id=challenge_id).first()
    if deployment is None:
        while True:
            port = random.randint(PORT_START, PORT_END)
            port_exists = Deployment.query.filter_by(port=port).first()
            if port_exists is None:
                break

        id = deploy(challenge_id, port)
        deployment = Deployment(id, user_id, challenge_id, port)
        db.session.add(deployment)
        db.session.commit()
        return jsonify({"status":"success", "url": f"{HOST_IP}:{port}/"})
    else:
        print(deployment)
        return jsonify({"status":"success", "url" : f"{HOST_IP}:{deployment.port}/"})

    
@app.route('/kill', methods=['POST'])
@jwt_verification(["challenge_id", "user_id"])
def kill_challenge(challenge_id, user_id):
    deployment = Deployment.query.filter_by(user_id=user_id, challenge_id=challenge_id).first()
    if deployment is not None:
        remove_deployment(deployment.deployment_id)
        return jsonify({"status":"success"})
    else:
        return jsonify({'status':'fail', 'message': 'No such deployment.'}), 404
        
db.create_all()
auto_clear()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=APP_PORT, debug=True) 