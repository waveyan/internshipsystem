from flask import render_template,request
from . import main
from ..models import Permission
from ..api_1_0.errors import bad_request,forbidden


@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response=bad_request('not found')
        return response
    return render_template('404.html',Permission=Permission), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response=forbidden('forbidden')
        return response
    return render_template('500.html',Permission=Permission), 500
