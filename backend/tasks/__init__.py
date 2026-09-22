from flask import Blueprint

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

from . import routes
