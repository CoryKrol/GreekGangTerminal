from flask import jsonify, request, g, url_for, current_app

from . import api
from .decorators import permission_required
from .errors import forbidden
from .. import db
from ..models import Stock, Trade, Permission


@api.route('/trades/')
def get_trades():
    page = request.args.get('page', 1, type=int)
    pagination = Trade.query.paginate(
        page, per_page=current_app.config['TRADES_PER_PAGE'],
        error_out=False)
    trades = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_trades', page=page-1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_trades', page=page+1)
    return jsonify({
        'trades': [trade.to_json() for trade in trades],
        'prev': prev,
        'next': next_page,
        'count': pagination.total
    })


@api.route('/trades/<int:trade_id>')
def get_trade(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    return jsonify(trade.to_json())


@api.route('/trades/', methods=['POST'])
@permission_required(Permission.WRITE)
def new_trade():
    trade = Trade.from_json(request.json)
    trade.author = g.current_user
    db.session.add(trade)
    db.session.commit()
    return jsonify(trade.to_json()), 201, \
        {'Location': url_for('api.get_trade', trade_id=trade.id)}


@api.route('/trades/<int:trade_id>', methods=['PUT'])
@permission_required(Permission.WRITE)
def edit_trade(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    if g.current_user != trade.user and \
            not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permissions.')
    trade.stock = Stock.query.filter_by(ticker=request.json.get('stock', trade.stock.ticker)).first()
    trade.quantity = request.json.get('quantity', trade.quantity)
    trade.price = request.json.get('price', trade.price)
    db.session.add(trade)
    db.session.commit()
    return jsonify(trade.to_json())
