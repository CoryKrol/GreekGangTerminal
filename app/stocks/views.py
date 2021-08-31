from flask import abort, current_app, render_template, flash, redirect, request, url_for
from flask_login import current_user, login_required
from typing import Final

from . import stocks
from .forms import AddStockForm, EditStockForm
from .. import db, photos
from ..main.forms import SearchForm
from ..decorators import admin_required
from ..models import Stock, Trade

STOCK_INFO: Final = '.stock_info'


@stocks.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_stock():
    search_form = SearchForm()
    form = AddStockForm()
    if form.validate_on_submit():
        new_stock = Stock(ticker=form.ticker.data,
                          name=form.name.data,
                          photo_filename=photos.save(form.photo.data),
                          is_active=form.active.data,
                          sector=form.sector.data,
                          year_high=form.year_high.data,
                          year_low=form.year_low.data)
        db.session.add(new_stock)
        db.session.commit()
        flash('Profile for ' + new_stock.name + ' created successfully.')
        return redirect(url_for(STOCK_INFO, ticker=new_stock.ticker, search_form=search_form))
    return render_template('stocks/edit_stock.html', form=form, search_form=search_form)


@stocks.route('/edit/<ticker>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_stock(ticker):
    search_form = SearchForm()
    stock = Stock.query.filter_by(ticker=ticker).first()
    if stock is None:
        abort(404)
    form = EditStockForm(stock=stock)
    form.photo.data = None
    if form.validate_on_submit():
        stock.ticker = form.ticker.data
        stock.name = form.name.data
        if form.photo.data is not None:
            stock.photo_filename = photos.save(form.photo.data)
        stock.is_active = form.active.data
        stock.sector = form.sector.data
        stock.year_high = form.year_high.data
        stock.year_low = form.year_low.data
        db.session.add(stock)
        db.session.commit()
        flash('Profile for ' + stock.name + ' updated successfully.')
        return redirect(url_for(STOCK_INFO, ticker=stock.ticker, search_form=search_form))
    form.ticker.data = stock.ticker
    form.name.data = stock.name
    form.active.data = stock.is_active
    form.sector.data = stock.sector
    form.year_high.data = stock.year_high
    form.year_low.data = stock.year_low
    return render_template('stocks/edit_stock.html', form=form, stock=stock, search_form=search_form)


@stocks.route('/<ticker>')
@login_required
def stock_info(ticker):
    search_form = SearchForm()
    stock = Stock.query.filter_by(ticker=ticker).first()
    if stock is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    pagination = stock.trades.order_by(Trade.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['TRADES_PER_PAGE'],
        error_out=False)
    trades = pagination.items
    return render_template('stocks/stock_info.html', stock=stock, trades=trades, pagination=pagination, search_form=search_form)


@stocks.route('/watch/<ticker>')
@login_required
def watch(ticker):
    search_form = SearchForm()
    stock = Stock.query.filter_by(ticker=ticker).first()
    if stock is None:
        flash('Invalid ticker.')
        return redirect(url_for('.index'))
    if current_user.is_watching(stock):
        flash('Already watching stock.')
        return redirect(url_for(STOCK_INFO, ticker=ticker, search_form=search_form))
    current_user.watch(stock)
    db.session.commit()
    flash('You are now watching %s.' % stock.name)
    return redirect(url_for(STOCK_INFO, ticker=ticker, search_form=search_form))


@stocks.route('/unwatch/<ticker>')
@login_required
def unwatch(ticker):
    search_form = SearchForm()
    stock = Stock.query.filter_by(ticker=ticker).first()
    if stock is None:
        flash('Invalid ticker.')
        return redirect(url_for('.index'))
    if not current_user.is_watching(stock):
        flash('Not watching stock.')
        return redirect(url_for(STOCK_INFO, ticker=ticker, search_form=search_form))
    current_user.unwatch(stock)
    db.session.commit()
    flash('You are not watching %s anymore.' % stock.name)
    return redirect(url_for(STOCK_INFO, ticker=ticker, search_form=search_form))


@stocks.route('/viewAllStocks')
@login_required
def view_all_stocks():
    search_form = SearchForm()
    stocks_list = Stock.query.all()
    return render_template('stocks/view_all_stocks.html', stocks=stocks_list, search_form=search_form)