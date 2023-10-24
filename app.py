from flask import Flask, request
import boto3
import psycopg2
from werkzeug.utils import secure_filename
from flask_cors import CORS
from decouple import config

app = Flask(__name__)
CORS(app)  # Esto habilitará CORS para todas las rutas

# Configuración de AWS S3
s3 = boto3.client(
    's3',
    aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
    region_name='us-east-1'
)

# Configuración de PostgreSQL
conn = psycopg2.connect(
    host='databaseyesith.ckzvzj2sfuyk.us-east-1.rds.amazonaws.com',
    database='databaseyesith',
    user='postgres',
    password='databaseyesith',
    port=5432  # El puerto por defecto de PostgreSQL
)

cur = conn.cursor()

# Crear la tabla 'archivo' si no existe
try:
    cur.execute('CREATE TABLE IF NOT EXISTS archivo (id SERIAL PRIMARY KEY, filename VARCHAR(255), urlfile VARCHAR(255))')
    conn.commit()
except Exception as e:
    print(f'Error {e}')
    conn.rollback()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'Falta el archivo en la solicitud', 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    
    # Guardar el archivo en S3
    s3.upload_fileobj(
        file,
        'bucketallerawsyesith',
        'uploads/' + filename,
        ExtraArgs={'ACL': 'public-read'}
    )

    urlfile = f'https://bucketallerawsyesith.s3.amazonaws.com/uploads/{filename}'

    # Guardar los datos en la base de datos
    try:
        cur.execute('INSERT INTO archivo (filename, urlfile) VALUES (%s, %s)', (filename, urlfile))
        conn.commit()
    except Exception as e:
        print(f'Error {e}')
        conn.rollback()

    return 'Archivo subido y registrado correctamente', 200

@app.route('/list', methods=['GET'])
def list_files():
    try:
        cur.execute('SELECT * FROM archivo')
        rows = cur.fetchall()
        return {'files': rows}, 200
    except Exception as e:
        print(f'Error {e}')
        conn.rollback()
        return 'Error interno del servidor', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

