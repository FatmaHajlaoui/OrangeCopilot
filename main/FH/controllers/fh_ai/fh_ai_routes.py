from flask import Blueprint, render_template

fh_ai_bp = Blueprint(
    'fh_ai_bp', __name__,
    static_folder='static',
    template_folder='templates'
)


@fh_ai_bp.route('/ai/risk')
def ai_risk_page():
    return render_template("FH/fh_ai/ai_risk.html")