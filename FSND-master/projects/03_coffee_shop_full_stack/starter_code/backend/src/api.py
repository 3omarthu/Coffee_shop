import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth


app = Flask(__name__)
setup_db(app)
CORS(app)


@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header['Access-Control-Allow-Headers'] = 'Authorization,Content-Type,true'
    header['Access-Control-Allow-Methods'] = 'POST,GET,PUT,DELETE,PATCH,OPTIONS'
    return response

db_drop_and_create_all()

# ROUTES


@app.route('/drinks')
def get_drink():
    try:
        drinks = list(map(Drink.short, Drink.query.all()))
        result = {
            "success": "true",
            "drinks": drinks
        }
        return jsonify(result)
    except:
        abort(422)


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinkdetail(token):
    try:
        drinks = list(map(Drink.long, Drink.query.all()))
        result = {
            "success": "true",
            "drinks": drinks
        }
        return jsonify(result)
    except:
        abort(500)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drink(token):
    data = request.get_json()

    if not ('title' in data and 'recipe' in data):
        abort(422)

    title = data.get('title', None)
    recipe = data.get('recipe', None)

    drink = Drink(title=title, recipe=json.dumps(recipe))

    try:
        Drink.insert(drink)
        newDrink = Drink.query.filter_by(id=drink.id).first()
    except:
        abort(500)

    return jsonify({
        'success': "true",
        'drinks': [newDrink.long()]
    })


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(token, drink_id):
    data = request.get_json()
    if not ('title' in data):
        abort(422)
    newTitle = data.get('title', None)
    drink = Drink.query.filter_by(id=drink_id).one_or_none()
    if drink is None:
        abort(404)

    if newTitle is None:
        abort(400)
    else:
        drink.title = newTitle

    drink.update()
    try:
        updatedDrink = Drink.query.filter_by(id=drink_id).first()
    except:
        abort(500)

    return jsonify({
        'success': "true",
        'drinks': [updatedDrink.long()]
    })


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(token, drink_id):
    try:
        drink = Drink.query.filter_by(id=drink_id).one_or_none()
    except:
        abort(500)

    if drink is None:
        abort(404)

    drink.delete()
    return jsonify({
        'success': "True",
        'deleted': drink_id
        })


# Error Handling


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad Request"
    }), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Not found"
    }), 404


@app.errorhandler(422)
def unprocessabley(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "Unprocessable"
    }), 422


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Internal Server Error"
    }), 500


@app.errorhandler(401)
def Unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unauthorized"
    }), 401

if __name__ == '__main__':
    app.run(port=8080, debug=True)
