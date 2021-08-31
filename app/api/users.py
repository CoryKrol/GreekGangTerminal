from flask import abort, g, jsonify, request, current_app, url_for

from . import api
from ..exceptions import ValidationError
from ..models import User, Stock, Trade, Watch


@api.route('/users/<username>')
def get_user(username):
    user = User.find_by_username_or_404(username=username)
    return jsonify(user.to_json())


@api.route('/users/<username>/trades/')
def get_user_trades(username):
    user = User.find_by_username_or_404(username=username)
    page = request.args.get('page', 1, type=int)
    pagination = user.trades.order_by(Trade.timestamp.desc()).paginate(
        page, per_page=current_app.config['TRADES_PER_PAGE'],
        error_out=False)
    trades = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_trades', id=id, page=page - 1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_user_trades', id=id, page=page + 1)
    return jsonify({
        'trades': [trade.to_json() for trade in trades],
        'prev': prev,
        'next': next_page,
        'count': pagination.total
    })


@api.route('/users/<username>/timeline/')
def get_user_followed_trades(username):
    user = User.find_by_username_or_404(username=username)
    if g.current_user is not user:
        abort(403)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_trades.order_by(Trade.timestamp.desc()).paginate(
        page, per_page=current_app.config['TRADES_PER_PAGE'],
        error_out=False)
    trades = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_followed_trades', username=username, page=page - 1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_user_followed_trades', username=username, page=page + 1)
    return jsonify({
        'trades': [trade.to_json() for trade in trades],
        'prev': prev,
        'next': next_page,
        'count': pagination.total
    })


@api.route('/users/<username>/watch/<ticker>')
def user_watch_stock(username, ticker):
    user = User.find_by_username_or_404(username=username)
    if g.current_user is not user:
        abort(403)
    stock = Stock.query.filter_by(ticker=ticker).first()
    if stock is None:
        abort(404)
    if user.is_watching(stock=stock):
        raise ValidationError('user is already watching stock')
    user.watch(stock=stock)
    new_watch = user.watches.filter_by(stock_id=stock.id).first()
    return jsonify(new_watch.to_json()), 201, {'Location': url_for('api.user_unwatch_stock',
                                                                   username=username,
                                                                   ticker=ticker)}


@api.route('/users/<username>/unwatch/<ticker>')
def user_unwatch_stock(username, ticker):
    user = User.find_by_username_or_404(username=username)
    if g.current_user is not user:
        abort(403)
    stock = Stock.query.filter_by(ticker=ticker).first()
    if stock is None:
        abort(404)
    if not user.is_watching(stock=stock):
        raise ValidationError('user is not watching stock')
    user.unwatch(stock=stock)
    return {}, 204


@api.route('/users/<username>/watchlist/')
def get_user_watched_stocks(username):
    user = User.find_by_username_or_404(username=username)
    if g.current_user is not user:
        abort(403)
    page = request.args.get('page', 1, type=int)
    pagination = user.watches.order_by(Watch.timestamp.desc()).paginate(
        page, per_page=current_app.config['WATCHLIST_PER_PAGE'],
        error_out=False)
    watches = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_watched_stocks', username=username, page=page - 1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_user_watched_stocks', username=username, page=page + 1)
    return jsonify({
        'stocks': [watch.to_json() for watch in watches],
        'prev': prev,
        'next': next_page,
        'count': pagination.total
    }), 200
