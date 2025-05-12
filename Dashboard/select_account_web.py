"""
Select Account Web Module

This file provides a Flask application for selecting an account environment (demo or live).

Enhancements:
- Added detailed comments for better understanding.
- Improved error handling and logging.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from src.Exchanges.capital_com_api.select_account import (
    login_to_capital, fetch_accounts, save_account_to_db, DEMO_SERVER, LIVE_SERVER
)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# File-level comment: This module handles account environment selection for the Capital.com API.

@app.route('/')
def index():
    """
    Render the index page.

    Returns:
        str: Rendered HTML template for the index page.
    """
    return render_template('index.html')

@app.route('/select_environment', methods=['GET', 'POST'])
def select_environment():
    """
    Handle account environment selection (demo or live).

    Returns:
        str: Redirects to the index page or renders the selection page.
    """
    if request.method == 'POST':
        environment = request.form.get('environment')
        if environment == 'demo':
            server = DEMO_SERVER
        elif environment == 'live':
            server = LIVE_SERVER
        else:
            flash("Invalid environment selected.", "error")
            return redirect(url_for('index'))

        try:
            # Perform login and fetch accounts
            session_tokens = login_to_capital(server)
            accounts = fetch_accounts(server, session_tokens)
            if not accounts:
                flash('No accounts found', 'error')
                return redirect(url_for('index'))
            return render_template('select_account.html', accounts=accounts, server=server)
        except Exception as e:
            flash(f"Error selecting environment: {e}", "error")
            app.logger.error(f"Error in select_environment: {e}")
            return redirect(url_for('index'))

    return render_template('select_environment.html')

@app.route('/select_account', methods=['POST'])
def select_account():
    """
    Handle account selection.

    Returns:
        str: Redirects to the index page after saving the account.
    """
    account_id = request.form.get('account_id')
    server = request.form.get('server')

    if not account_id or not server:
        flash('Invalid account selection', 'error')
        return redirect(url_for('index'))

    try:
        # Fetch account details from the form
        account = {
            'accountId': account_id,
            'accountName': request.form.get('account_name'),
            'balance': {'balance': float(request.form.get('balance'))},
            'currency': request.form.get('currency')
        }
        save_account_to_db(account, server)
        flash(f'Successfully selected account: {account["accountName"]}', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        app.logger.error(f"Error in select_account: {e}")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
