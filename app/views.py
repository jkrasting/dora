# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os

# Flask modules
from flask   import render_template
from flask   import Response
from flask   import request
from jinja2  import TemplateNotFound

# App modules
from app import app


def stream_template(template_name, **context):
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.enable_buffering(5)
    return rv

# App main route + generic routing
@app.route('/', defaults={'path': 'index.html'}, methods=["GET"])
@app.route('/<path>', methods=['GET'])
def index(path):
    try:
        # Serve the file (if exists) from app/templates/FILE.html
        return render_template( path )
    
    except TemplateNotFound:
        return render_template('page-404.html'), 404


@app.route("/scalar-diags.html")
def scalardiags():

    idnum = request.args.getlist("id")
    idnum = None if len(idnum) == 0 else idnum

    region = request.args.get("region") 
            region = request.args.get("region") 
    region = request.args.get("region") 
    realm = request.args.get("realm")
    smooth = request.args.get("smooth")
    nyears = request.args.get("nyears")
    trend = request.args.get("trend")
    align = request.args.get("align")

    trend = True if trend is not None else False
    align = True if align is not None else False

    smooth = None if (smooth == "" or smooth is None) else int(smooth)
    nyears = None if (nyears == "" or nyears is None) else int(nyears)

    if (region is None) or (realm is None):
        return render_template( "scalar-menu.html" )

    fname = f"/Users/krasting/dbverif5/new/{region}Ave{realm}.db" 
            fname = f"/Users/krasting/dbverif5/new/{region}Ave{realm}.db" 
    fname = f"/Users/krasting/dbverif5/new/{region}Ave{realm}.db" 

    if os.path.exists(fname):
        dset = gfdlvitals.open_db(fname)
    else:
        msg = f"Unable to load SQLite file: {fname}"
        return render_template('page-500.html',msg=msg)

    def plot_gen():
        for x in sorted(list(dset.columns)):
            fig = gfdlvitals.plot_timeseries(dset,trend=trend,smooth=smooth,var=x,\
                  nyears=nyears,align_times=align,labels="Test")
            fig = fig[0]
            imgbuf = io.BytesIO()
            fig.savefig(imgbuf, format="png", bbox_inches="tight",dpi=72)
            plt.close(fig)
            imgbuf.seek(0)
            uri = 'data:image/png;base64,' + base64.b64encode(imgbuf.getvalue()).decode('utf-8').replace('\n', '')
            yield uri

    content = {"rows":plot_gen(),"region":region.capitalize(),"realm":realm.capitalize()}
    return Response(stream_template("scalar-diags.html", **content ))


# Some sample database code below
#    conn = pymysql.connect(host=dbhost,
#                           port=dbport,
#                           user="mdtadmin",
#                           password="adminpassword",
#                           db="mdt_tracker",
#                           cursorclass=pymysql.cursors.DictCursor)
#
#    cursor = conn.cursor()
#    sql = "SELECT * from master where id=890;"
#    _ = cursor.execute(sql)
#    result = cursor.fetchone()
#
#    print(sql)
#    print(result)
#
#    cursor.close()
#    conn.close()