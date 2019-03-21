from flask import Blueprint, render_template

static_blueprint: Blueprint = Blueprint(
    name="static_pages", import_name=__name__, template_folder="templates"
)


@static_blueprint.route("/")
def index():
    return render_template("index.html")
