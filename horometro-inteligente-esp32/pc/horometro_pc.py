#!/usr/bin/env python3
"""Puente USB/web local. Python 3.10+. Ejecutar: python horometro_pc.py --port COM5"""
import argparse
import json
import secrets
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOKEN = secrets.token_urlsafe(24)


class Monitor:
    def __init__(self, history_path=ROOT / 'historial.json'):
        self.lock = threading.RLock()
        self.serial_lock = threading.Lock()
        self.serial = None
        self.command_lock = threading.Lock()
        self.pending = {}
        self.last_seen = 0.0
        self.status = None
        self.error = 'Esperando datos de la ESP32'
        self.path = Path(history_path)
        self.history_error = ''
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data.get('seen'), dict) or not isinstance(data.get('events'), list):
                raise ValueError('Formato de historial incorrecto')
            self.history = data
        except FileNotFoundError:
            self.history = {'seen': {}, 'events': []}
        except (ValueError, OSError) as exc:
            self.history = {'seen': {}, 'events': []}
            self.history_error = 'No se pudo leer historial.json: ' + str(exc)

    def save_history(self):
        try:
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps(self.history, ensure_ascii=False, indent=2), encoding='utf-8')
            temporary.replace(self.path)
            self.history_error = ''
        except OSError as exc:
            self.history_error = 'No se pudo guardar el historial: ' + str(exc)

    def accept(self, obj):
        if obj.get('type') == 'reply':
            with self.lock:
                slot = self.pending.get(obj.get('id'))
                if slot:
                    slot[1].append(obj)
                    slot[0].set()
            return
        if obj.get('type') != 'status':
            if obj.get('error'):
                with self.lock:
                    self.error = str(obj['error'])
            return
        if not isinstance(obj.get('device'), str) or not isinstance(obj.get('on'), bool):
            raise ValueError('Estado invalido')
        for field in ('generation', 'total_us', 'us_per_hour', 'interval_hours', 'alert_index'):
            if type(obj.get(field)) is not int or obj[field] < 0:
                raise ValueError('Campo invalido: ' + field)
        if not obj['us_per_hour'] or not obj['interval_hours']:
            raise ValueError('Escala invalida')
        if obj['alert_index'] != obj['total_us'] // (obj['us_per_hour'] * obj['interval_hours']):
            raise ValueError('Umbral inconsistente')
        key = f"{obj['device']}:{obj['generation']}:{obj['us_per_hour']}:{obj['interval_hours']}"
        if obj.get('schedule', 0):
            key += ':' + str(obj['schedule'])
        with self.lock:
            self.status = obj
            self.last_seen = time.monotonic()
            self.error = ''
            index = obj['alert_index']
            seen = int(self.history['seen'].get(key, obj.get('baseline_index', 0)))
            if index > seen:
                # Si hubo desconexion, resumir umbrales pendientes en una alerta.
                hours = index * obj['interval_hours']
                skipped = index - seen
                msg = f'Equipo DEMO-01: {hours} horas acumuladas. Corresponde revision de mantenimiento.'
                if skipped > 1:
                    msg += f' Se alcanzaron {skipped} umbrales desde el ultimo registro.'
                event = {'id': f'{key}:{index}', 'at': datetime.now().astimezone().isoformat(timespec='seconds'),
                         'hours': hours, 'message': msg}
                self.history['events'].append(event)
                self.history['events'] = self.history['events'][-100:]
                self.history['seen'][key] = index
                self.save_history()

    def snapshot(self):
        with self.lock:
            connected = self.status is not None and time.monotonic() - self.last_seen < 3
            return {'connected': connected, 'status': self.status,
                    'error': self.error, 'history_error': self.history_error,
                    'events': list(self.history['events'])}

    def command(self, action, value=None):
        with self.command_lock:
            with self.lock:
                s = self.status
                if not s or time.monotonic()-self.last_seen >= 3:
                    raise ValueError('La ESP32 no está conectada')
                if s.get('protocol') != 2:
                    raise ValueError('Cargue el firmware con interruptor de este paquete')
                if action == 'reset':
                    command = 'RESET'
                elif action == 'ack':
                    if type(value) is not int or not 0 <= value <= s['alert_index']:
                        raise ValueError('Aviso inválido')
                    command = f'ACK {value}'
                elif action == 'interval' and type(value) is int and 1 <= value <= 1000000:
                    command = f'INTERVAL {value}'
                else:
                    raise ValueError('Indique horas enteras entre 1 y 1000000')
                ident = secrets.randbits(32)
                done, answers = threading.Event(), []
                self.pending[ident] = (done, answers)
            try:
                with self.serial_lock:
                    if self.serial is None:
                        raise ValueError('Puerto USB no disponible')
                    self.serial.write(f'{ident} {command}\n'.encode('ascii'))
                if not done.wait(3):
                    raise ValueError('Sin confirmación; revise el estado antes de repetir')
                if not answers[0].get('ok'):
                    raise ValueError(answers[0]['message'])
                return answers[0]['message']
            finally:
                with self.lock:
                    self.pending.pop(ident, None)

    def reader(self, port):
        import serial
        while True:
            try:
                # Abrir el puerto puede reiniciar automaticamente la DevKit.
                with serial.Serial(port, 115200, timeout=1, write_timeout=1) as connection:
                    with self.serial_lock:
                        self.serial = connection
                    while True:
                        line = connection.readline(1024)
                        if not line:
                            continue
                        try:
                            obj = json.loads(line.decode('utf-8'))
                            if isinstance(obj, dict):
                                self.accept(obj)
                        except (UnicodeError, ValueError, KeyError, TypeError):
                            pass  # Ignorar textos de arranque y tramas incompletas.
            except (serial.SerialException, OSError) as exc:
                with self.lock:
                    self.last_seen = 0
                    self.error = 'USB: ' + str(exc)
            finally:
                with self.serial_lock:
                    self.serial = None
            time.sleep(2)


def make_handler(monitor):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def reply(self, code, body, content_type='application/json; charset=utf-8'):
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/':
                page = (ROOT / 'panel.html').read_text(encoding='utf-8').replace('__TOKEN__', TOKEN)
                self.reply(200, page.encode('utf-8'), 'text/html; charset=utf-8')
            elif self.path == '/api/state':
                self.reply(200, json.dumps(monitor.snapshot()).encode('utf-8'))
            else:
                self.reply(404, b'{}')

        def do_POST(self):
            if self.path not in ('/api/reset','/api/ack','/api/interval'):
                self.reply(404, b'{}')
                return
            if self.headers.get('X-Demo-Token') != TOKEN:
                self.reply(403, b'{}')
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 <= size <= 512: raise ValueError('Solicitud demasiado larga')
                body = json.loads(self.rfile.read(size) or b'{}')
                if not isinstance(body, dict): raise ValueError('Solicitud inválida')
                message = monitor.command(self.path.rsplit('/',1)[1], body.get('value'))
                self.reply(200, json.dumps({'ok':True,'message':message}).encode())
            except (ValueError, OSError) as exc:
                self.reply(409, json.dumps({'error': str(exc)}).encode('utf-8'))
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', help='Puerto USB, por ejemplo COM5 o /dev/ttyUSB0')
    parser.add_argument('--ports', action='store_true', help='Mostrar puertos disponibles')
    parser.add_argument('--http-port', type=int, default=8000)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    try:
        from serial.tools import list_ports
    except ImportError:
        parser.exit(1, 'Falta pyserial. Ejecuta: python -m pip install -r requirements.txt\n')
    if args.ports:
        for port in list_ports.comports():
            print(f'{port.device}: {port.description}')
        return
    if not args.port:
        parser.error('Indica --port COM5. Usa --ports para listar los puertos.')
    monitor = Monitor()
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.http_port), make_handler(monitor))
    except OSError as exc:
        parser.exit(1, f'No se pudo abrir la pagina local: {exc}\nPrueba --http-port 8001\n')
    threading.Thread(target=monitor.reader, args=(args.port,), daemon=True).start()
    url = f'http://127.0.0.1:{args.http_port}'
    print(f'Horometro: {url}\nMantener este programa abierto. Salir: Ctrl+C.')
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
