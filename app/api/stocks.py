from flask import abort, jsonify, request, url_for, current_app

from . import api
from .decorators import permission_required
from .. import db
from ..exceptions import ValidationError
from ..models import Stock, Permission


@api.route('/stocks/')
def get_stocks():
    page = request.args.get('page', 1, type=int)
    pagination = Stock.query.paginate(page, per_page=current_app.config['STOCKS_PER_PAGE'], error_out=False)
    stocks = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_stocks', page=page-1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_stocks', page=page+1)
    return jsonify({
        'stocks': [stock.to_json() for stock in stocks],
        'prev': prev,
        'next': next_page,
        'count': pagination.total
    })


@api.route('/stocks/<ticker>')
def get_stock(ticker):
    stock = Stock.query.filter_by(ticker=ticker).first()
    if stock is None:
        abort(404)
    return jsonify(stock.to_json())


@api.route('/stocks/', methods=['POST'])
@permission_required(Permission.ADMIN)
def new_stock():
    stock = Stock.from_json(request.json)
    if Stock.query.filter_by(ticker=stock.ticker).first() is not None:
        raise ValidationError('Stock with %s already exists.' % stock.ticker)
    db.session.add(stock)
    db.session.commit()
    return jsonify(stock.to_json()), 201, \
        {'Location': url_for('api.get_stock', ticker=stock.ticker)}


@api.route('/stocks/<ticker>', methods=['PUT'])
@permission_required(Permission.ADMIN)
def edit_stock(ticker):
    stock1 = Stock.query.filter_by(ticker=ticker).first()
    if stock1 is None:
        abort(404)
    stock1.ticker = request.json.get('ticker', stock1.ticker)
    stock2 = Stock.query.filter_by(ticker=stock1.ticker).first()
    if stock2 is not None and stock1.id is not stock2.id:
        raise ValidationError('Stock with %s already exists.' % stock1.ticker)
    stock1.name = request.json.get('name', stock1.name)
    stock1.sector = request.json.get('sector', stock1.sector)
    stock1.year_high = request.json.get('year_high', stock1.year_high)
    stock1.year_low = request.json.get('year_low', stock1.year_low)
    db.session.add(stock1)
    db.session.commit()
    return jsonify(stock1.to_json())
