import os
import datetime
import logging

from flask import Flask, render_template, request, Response
import sqlalchemy

app = Flask(__name__)

# @app.route('/')
# def hello_world():
#     target = os.environ.get('TARGET', 'World')
#     return 'Hello {}!\n'.format(target)

# connection name: mcarolyn-intern-project-2019:us-central1:myinstance

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))

# Remember - storing secrets in plaintext is potentially unsafe. Consider using
# something like https://cloud.google.com/kms/ to help keep secrets secret.
db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASS")
db_name = os.environ.get("DB_NAME")
cloud_sql_connection_name = "mcarolyn-intern-project-2019:us-central1:myinstance"

app = Flask(__name__)

logger = logging.getLogger()
logger.setLevel(10)

# [START cloud_sql_mysql_sqlalchemy_create]
# The SQLAlchemy engine will help manage interactions, including automatically
# managing a pool of connections to your database
db = sqlalchemy.create_engine(
    # Equivalent URL:
    # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_sock=/cloudsql/<cloud_sql_instance_name>
    sqlalchemy.engine.url.URL(
        drivername='mysql+pymysql',
        username=db_user,
        password=db_pass,
        database=db_name,
        query={
            'unix_socket': '/cloudsql/{}'.format(cloud_sql_connection_name)
        }
    ),
    # ... Specify additional properties here.
    # [START_EXCLUDE]

    # [START cloud_sql_mysql_sqlalchemy_limit]
    # Pool size is the maximum number of permanent connections to keep.
    pool_size=5,
    # Temporarily exceeds the set pool_size if no connections are available.
    max_overflow=2,
    # The total number of concurrent connections for your application will be
    # a total of pool_size and max_overflow.
    # [END cloud_sql_mysql_sqlalchemy_limit]

    # [START cloud_sql_mysql_sqlalchemy_backoff]
    # SQLAlchemy automatically uses delays between failed connection attempts,
    # but provides no arguments for configuration.
    # [END cloud_sql_mysql_sqlalchemy_backoff]

    # [START cloud_sql_mysql_sqlalchemy_timeout]
    # 'pool_timeout' is the maximum number of seconds to wait when retrieving a
    # new connection from the pool. After the specified amount of time, an
    # exception will be thrown.
    pool_timeout=30,  # 30 seconds
    # [END cloud_sql_mysql_sqlalchemy_timeout]

    # [START cloud_sql_mysql_sqlalchemy_lifetime]
    # 'pool_recycle' is the maximum number of seconds a connection can persist.
    # Connections that live longer than the specified amount of time will be
    # reestablished
    pool_recycle=1800,  # 30 minutes
    # [END cloud_sql_mysql_sqlalchemy_lifetime]

    # [END_EXCLUDE]
)
# [END cloud_sql_mysql_sqlalchemy_create]


# @app.before_first_request
# def create_tables():
#     # Create tables (if they don't already exist)
#     with db.connect() as conn:
#         conn.execute(
#             "CREATE TABLE IF NOT EXISTS votes "
#             "( vote_id SERIAL NOT NULL, time_cast timestamp NOT NULL, "
#             "candidate CHAR(6) NOT NULL, PRIMARY KEY (vote_id) );"
#         )


@app.route('/', methods=['GET'])
def index():
    logging.log(10,"entered get function")
    with db.connect() as conn:
        # Execute the query and fetch all results
        guests = conn.execute(
            "SELECT * FROM entries"
        ).fetchall()
    guestlist = []
    for guest in guests:
        # first column of table is name, second column is message
        guestlist.append({'name': guest[0], 'message': guest[1]})
    
    #return str(guests)
    return render_template(
        'index.html',
        guestlist=guestlist,
    )
    
@app.route('/', methods=['POST'])
def add_entry():
    logging.log(10,"entered post function")
    # return str(request.form)
    name = request.form['user_name']
    message = request.form['user_message']
    
    stmt = sqlalchemy.text(
        "INSERT INTO entries (guestName, content)"
        " VALUES (:name, :message)"
    )
    try:
        # Using a with statement ensures that the connection is always released
        # back into the pool at the end of statement (even if an error occurs)
        with db.connect() as conn:
            conn.execute(stmt, name=name, message=message)
    except Exception as e:
        # If something goes wrong, handle the error in this section. This might
        # involve retrying or adjusting parameters depending on the situation.
        # [START_EXCLUDE]
        logger.exception(e)
        return Response(
            status=500,
            response="Unable to successfully submit message! Please check the "
                     "application logs for more details."
        )
        # [END_EXCLUDE]
    # [END cloud_sql_mysql_sqlalchemy_connection]

    return render_template(
        'added.html',
        name=name,
        message=message,
    )

#    return Response(
#        status=200,
#        response="Message '{}' successfully entered for '{}'".format(
#            message, name)
#    )
