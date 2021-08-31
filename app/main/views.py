import os.path

from flask import abort, current_app, make_response, render_template, redirect, request, url_for, send_from_directory
from flask_login import current_user, login_required

from . import main
from .forms import SearchForm
from ..models import User, Stock, Trade


@main.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    if form.validate_on_submit():
        return search(form=form)
    page = request.args.get('page', 1, type=int)
    show_followed_trades = False
    if current_user.is_authenticated:
        show_followed_trades = bool(request.cookies.get('show_followed_trades', ''))
    if show_followed_trades:
        query = current_user.followed_trades
    else:
        query = Trade.query
    pagination = query.order_by(Trade.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['TRADES_PER_PAGE'], error_out=False)
    trades = pagination.items
    return render_template('index.html',
                           trades=trades,
                           show_followed_trades=show_followed_trades,
                           pagination=pagination, search_form=form)


@main.route('/search', methods=['POST'])
def search(form):
    page = request.args.get('page', 1, type=int)
    if form.filter.data == 'stocks':
        pagination = Stock.query.whooshee_search(form.query.data).order_by(Stock.id.desc()).paginate(
            page,
            per_page=current_app.config['TRADES_PER_PAGE'], error_out=False)
        stocks = pagination.items
        return render_template('search_results.html',
                               stocks=stocks,
                               pagination=pagination,
                               search_form=form)
    else:
        pagination = User.query.whooshee_search(form.query.data).order_by(User.id.desc()).paginate(
            page,
            per_page=current_app.config['TRADES_PER_PAGE'], error_out=False)
        users = pagination.items
        return render_template('search_results.html',
                               users=users,
                               pagination=pagination,
                               search_form=form)


@main.route('/files/images/<path:file_path>')
def photos(file_path):
    directory = 'files/images/' + file_path
    dir_tuple = os.path.split(os.path.abspath(directory))
    if os.path.basename(dir_tuple[0]) != 'images':
        image_path = 'files/images/' + os.path.basename(dir_tuple[0])
    else:
        image_path = 'files/images'
    return send_from_directory(image_path, dir_tuple[1])


@main.route('/all')
@login_required
def show_all():
    """
    Cookies can only be set using responses, have to do it here instead of letting flask set it
    max_age is in seconds, without setting it the cookie expires when the browser closes
    """
    search_form = SearchForm()
    response = make_response(redirect(url_for('.index', search_form=search_form)))
    response.set_cookie('show_followed_trades', '', max_age=30*24*60*60)
    return response


@main.route('/followed')
@login_required
def show_followed():
    """
    Cookies can only be set using responses, have to do it here instead of letting flask set it
    max_age is in seconds, without setting it the cookie expires when the browser closes
    """
    search_form = SearchForm()
    response = make_response(redirect(url_for('.index', search_form=search_form)))
    response.set_cookie('show_followed_trades', '1', max_age=30*24*60*60)
    return response


@main.route('/shutdown')
def server_shutdown():
    """Used by unit tests to stop flask server"""
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'
