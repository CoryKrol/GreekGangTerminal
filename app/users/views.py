from flask import current_app, flash, render_template, redirect, request, url_for
from flask_login import current_user, login_required
from typing import Final

from . import users
from .forms import EditProfileAdministratorForm, EditProfileForm
from .. import db
from ..main.forms import SearchForm
from ..decorators import admin_required, permission_required
from ..models import Permission, Role, Trade, User

INDEX: Final = '.index'
INVALID_USER: Final = 'Invalid user.'
USER_PROFILE: Final = '.user_profile'


@users.route('/edit-profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    search_form = SearchForm()
    edit_user = User.query.get_or_404(user_id)
    form = EditProfileAdministratorForm(user=edit_user)
    if form.validate_on_submit():
        edit_user.about_me = form.about_me.data
        edit_user.confirmed = form.confirmed.data
        edit_user.email = form.email.data
        edit_user.location = form.location.data
        edit_user.name = form.name.data
        edit_user.role = Role.query.get(form.role.data)
        edit_user.username = form.username.data
        db.session.add(edit_user)
        db.session.commit()
        flash('Profile for ' + edit_user.username + ' updated successfully.')
        return redirect(url_for(USER_PROFILE, username=edit_user.username, search_form=search_form))
    form.about_me.data = edit_user.about_me
    form.confirmed.data = edit_user.confirmed
    form.email.data = edit_user.email
    form.location.data = edit_user.location
    form.name.data = edit_user.name
    form.role.data = edit_user.role_id
    form.username.data = edit_user.username
    return render_template('users/edit_profile.html', form=form, user=edit_user, search_form=search_form)


@users.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    search_form = SearchForm()
    form = EditProfileForm()
    if form.validate_on_submit():
        # Save submitted form
        current_user.about_me = form.about_me.data
        current_user.location = form.location.data
        current_user.name = form.name.data
        db.session.add(current_user)
        db.session.commit()
        flash('Profile successfully updated.')
        return redirect(url_for(USER_PROFILE, username=current_user.username, search_form=search_form))
    # Populate form with user data
    form.about_me.data = current_user.about_me
    form.location.data = current_user.location
    form.name.data = current_user.name
    return render_template('users/edit_profile.html', form=form, search_form=search_form)


@users.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    search_form = SearchForm()
    user = User.find_first_by_username(username=username)
    if user is None:
        flash(INVALID_USER)
        return redirect(url_for(INDEX, search_form=search_form))
    if current_user.is_following(user):
        flash('Already following user.')
        return redirect(url_for(USER_PROFILE, username=username, search_form=search_form))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following %s.' % username)
    return redirect(url_for(USER_PROFILE, username=username, search_form=search_form))


@users.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    search_form = SearchForm()
    user = User.find_first_by_username(username=username)
    if user is None:
        flash(INVALID_USER)
        return redirect(url_for(INDEX, search_form=search_form))
    if not current_user.is_following(user):
        flash('Not following user.')
        return redirect(url_for(USER_PROFILE, username=username, search_form=search_form))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following %s anymore.' % username)
    return redirect(url_for(USER_PROFILE, username=username, search_form=search_form))


@users.route('/followers/<username>')
@login_required
def followers(username):
    search_form = SearchForm()
    user = User.find_first_by_username(username=username)
    if user is None:
        flash(INVALID_USER)
        return redirect(url_for(INDEX, search_form=search_form))
    pagination = user.get_followers_pagination(request)
    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('users/followers.html',
                           user=user,
                           title="Followers of",
                           endpoint='.followers',
                           pagination=pagination,
                           follows=follows, search_form=search_form)


@users.route('/followed_by/<username>')
@login_required
def followed_by(username):
    search_form = SearchForm()
    user = User.find_first_by_username(username=username)
    if user is None:
        flash(INVALID_USER)
        return redirect(url_for(INDEX, search_form=search_form))
    pagination = user.get_followed_pagination(request)
    follows = [{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('users/followers.html',
                           user=user,
                           title="Followed by",
                           endpoint='.followed_by',
                           pagination=pagination,
                           follows=follows, search_form=search_form)


@users.route('/watchlist/')
@login_required
def watchlist():
    search_form = SearchForm()
    page = request.args.get('page', 1, type=int)
    pagination = current_user.watches.paginate(page, per_page=current_app.config['WATCHLIST_PER_PAGE'], error_out=False)
    watches = [{'stock': item.stock, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('users/watchlist.html',
                           user=current_user,
                           title='Watchlist',
                           endpoint='.watchlist',
                           pagination=pagination,
                           watches=watches, search_form=search_form)


@users.route('/<username>')
@login_required
def user_profile(username):
    search_form = SearchForm()
    user = User.find_by_username_or_404(username=username)
    trades = user.trades.order_by(Trade.timestamp.desc()).all()
    return render_template('users/user_profile.html', user=user, trades=trades, search_form=search_form)
