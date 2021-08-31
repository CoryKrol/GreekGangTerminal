import os
import sys
import click

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

from app import create_app, db
from app.models import Follow, Permission, Role, Stock, Trade, User
from flask_migrate import Migrate
from app import whooshee

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Follow=Follow, Permission=Permission, Role=Role, Stock=Stock, Trade=Trade, User=User)


@app.cli.command()
def reindex():
    whooshee.reindex()


@app.cli.command()
@click.option('--code-coverage/--no-code-coverage', default=False, help='Run tests with code coverage.')
@click.argument('test_names', nargs=-1)
def test(code_coverage, test_names):
    """
    Create a custom flask cli command to run the unit tests.
    Run with flask in terminal
    $ flask test
    """
    if code_coverage and not os.environ.get('FLASK_COVERAGE'):
        import subprocess
        os.environ['FLASK_COVERAGE'] = '1'
        sys.exit(subprocess.call(sys.argv))

    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        base_dir = os.path.abspath(os.path.dirname(__file__))
        coverage_dir = os.path.join(base_dir, 'tmp/coverage')
        COV.html_report(directory=coverage_dir)
        print('HTML version: file://%s/index.html' % coverage_dir)
        COV.erase()
