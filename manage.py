#!/usr/bin/env python
import os
from app import create_app, db
from app.models import Teacher, Role, Student, ComInfor, Journal, InternshipInfor, ComDirTea, SchDirTea
from flask.ext.script import Manager, Shell, Server
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app('default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, Teacher=Teacher, Role=Role, Student=Student, ComInfor=ComInfor,
                InternshipInfor=InternshipInfor, Journal=Journal)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

manager.add_command("runserver", Server(host = '0.0.0.0') )


if __name__ == '__main__':
    manager.run()
