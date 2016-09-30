from flask import Flask, jsonify, abort, g, redirect, url_for
from flask_restful import Resource, Api, reqparse, fields, marshal
from flask_restful.utils import cors
from flask_cors import CORS, cross_origin
import sqlite3, os

app = Flask(__name__)
api = Api(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# Cargar configuracion
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'libros.db'),
    DEBUG=True
))
app.config.from_envvar('APP_SETTINGS', silent=True)


def conexion_db():
    # Conecta a la base de datos
    con = sqlite3.connect(app.config['DATABASE'])
    con.row_factory = dict_factory
    return con

# Devuelve los datos en diccionario
def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_db():
    # Abrir una nueva conexion
    if not hasattr(g,'sqlite_db'):
        g.sqlite_db = conexion_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    # Cerrar la base de datos
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


# Funcion para la consulta de datos
def query_db(query, args=(), one=False, post=False):
    cur = get_db().execute(query, args)
    if(post):
        return get_db().commit()
    else:
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv

# Campos que se visualizaran
campos_libro = {
    'id': fields.Integer,
    'titulo': fields.String,
    'descripcion': fields.String,
    'uri': fields.Url('libro')
}


# Recurso
class LibrosAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('titulo', type=str, required=True,
                                   help='Sin titulo')
        self.reqparse.add_argument('descripcion', type=str, default="")
        super(LibrosAPI, self).__init__()

    # Funcion para mostrar todos los libros
    def get(self):
        libros = query_db('select * from libro')
        return {'libros': marshal(libros, campos_libro)}

    # Funcion para agregar un libro
    def post(self):
        args = self.reqparse.parse_args()
        if args['titulo'] != '':
            if args['descripcion'] != '':
                libro = query_db('insert into libro (titulo, descripcion) values (?, ?)', [args['titulo'], args['descripcion']], post=True)
                if libro is None:
                    return {'mensaje': 'El libro se agrego correctamente'}
        else:
            return {'error': 'No se pudo almacenar el libro.'}


class LibroAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('titulo', type=str, location='json')
        self.reqparse.add_argument('descripcion', type=str, location='json')
        super(LibroAPI, self).__init__()

    # Obtener libro
    def get(self, id):
        libro = query_db('select * from libro where id == ?', [id])
        if len(libro) == 0:
            abort(404)
        return {'libros': marshal(libro, campos_libro)}


api.add_resource(LibrosAPI, '/libros/', endpoint='libros')
api.add_resource(LibroAPI, '/libros/<int:id>', endpoint='libro')


if __name__ == '__main__':
    app.run(debug=True)
