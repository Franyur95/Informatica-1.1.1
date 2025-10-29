from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, date

app = Flask(__name__)

# --- Configuración y Persistencia de Datos ---
DATA_FILE = 'data.json'

def load_data():
    """Carga los datos de estudiantes y asistencia desde un archivo JSON."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Filtrar registros que no sean de hoy
            today_iso = date.today().isoformat()
            data['attendanceRecords'] = [
                r for r in data.get('attendanceRecords', [])
                if r['date'] == today_iso
            ]
            return {
                'students': data.get('students', []),
                'attendanceRecords': data.get('attendanceRecords', [])
            }
    return {'students': [], 'attendanceRecords': []}

def save_data(data):
    """Guarda los datos de estudiantes y asistencia en un archivo JSON."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# Inicializar datos al inicio
app_data = load_data()

# --- Rutas de Frontend ---
@app.route('/')
def index():
    return render_template('index.html')

# --- API ---
@app.route('/api/students', methods=['GET'])
def get_students():
    return jsonify(app_data['students'])

@app.route('/api/student/<dni>', methods=['GET'])
def get_student(dni):
    student = next((s for s in app_data['students'] if s['dni'] == dni), None)
    if student:
        return jsonify(student)
    return jsonify({'message':'Estudiante no encontrado'}), 404

@app.route('/api/register', methods=['POST'])
def register_student():
    data = request.json
    name = data.get('name', '').strip()
    dni = data.get('dni', '').strip()
    
    if not name or not dni or len(dni) != 8:
        return jsonify({'message':'Datos incompletos o DNI inválido.'}), 400

    if any(s['dni']==dni for s in app_data['students']):
        return jsonify({'message':'Este DNI ya está registrado.'}), 409

    new_student = {
        'id': len(app_data['students']) + 1,
        'name': name,
        'dni': dni,
        'grade': "Desarrollo de Software - 1er Año",
        'registeredAt': datetime.now().isoformat()
    }

    app_data['students'].append(new_student)
    save_data(app_data)
    return jsonify({'message':'Registro exitoso.', 'student': new_student}), 201

@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    dni = data.get('dni','').strip()

    student = next((s for s in app_data['students'] if s['dni']==dni), None)
    if not student:
        return jsonify({'message':'DNI no encontrado. Regístrate primero.'}), 404

    today_iso = date.today().isoformat()

    # Verificar si ya marcó asistencia hoy
    if any(r['studentDNI']==dni and r['date']==today_iso for r in app_data['attendanceRecords']):
        return jsonify({'message':'Ya marcaste asistencia hoy.'}), 409

    record = {
        'id': len(app_data['attendanceRecords']) + 1,
        'studentName': student['name'],
        'studentDNI': student['dni'],
        'studentGrade': student['grade'],
        'date': today_iso,
        'time': datetime.now().isoformat()
    }

    app_data['attendanceRecords'].append(record)
    save_data(app_data)
    return jsonify({'message':'Asistencia marcada correctamente.', 'record': record}), 201

@app.route('/api/attendance/today', methods=['GET'])
def get_today_attendance():
    today_iso = date.today().isoformat()
    today_records = [r for r in app_data['attendanceRecords'] if r['date']==today_iso]
    sorted_records = sorted(today_records, key=lambda x: x['time'], reverse=True)
    return jsonify(sorted_records)

# --- Limpiar asistencia (opcional manual) ---
@app.route('/api/attendance/clear', methods=['POST'])
def clear_attendance():
    today_iso = date.today().isoformat()
    app_data['attendanceRecords'] = [r for r in app_data['attendanceRecords'] if r['date']!=today_iso]
    save_data(app_data)
    return jsonify({'message':'Lista de asistencia de hoy reiniciada.'})

if __name__ == '__main__':
    # Guardar datos iniciales
    save_data(app_data)
    app.run(debug=True)
