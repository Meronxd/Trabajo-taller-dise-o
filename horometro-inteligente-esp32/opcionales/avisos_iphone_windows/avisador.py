"""Notificaciones locales usando el historial ya deduplicado del panel Windows."""
import json
import secrets
import time
from urllib import request
from urllib.parse import urlsplit
from pathlib import Path

BASE = Path(__file__).resolve().parent
PANEL = 'http://127.0.0.1:8000/api/state'
def save(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    tmp.replace(path)
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def fetch(url, payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    req = request.Request(url, data=body, headers={'Content-Type':'application/json'} if body else {})
    with request.urlopen(req, timeout=4) as res:
        return res.read()
def setup():
    file = BASE/'ajustes.json'
    if file.exists():
        return read(file)
    host = input('Direccion local de Home Assistant (ej.: http://192.168.1.50:8123): ').strip().rstrip('/')
    u = urlsplit(host)
    if u.scheme not in ('http','https') or not u.hostname or u.username or u.password or u.path or u.query or u.fragment:
        raise ValueError('Escriba solo la direccion del servidor, incluido http://')
    service = input('Accion de su iPhone (ej.: notify.mobile_app_iphone_de_meron): ').strip()
    import re
    if not re.fullmatch(r'notify\.mobile_app_[a-z0-9_]+', service):
        raise ValueError('La accion debe comenzar por notify.mobile_app_')
    key = secrets.token_urlsafe(32)
    yaml = """alias: Horómetro - aviso en iPhone
description: Solo recibe POST de la red local.
triggers:
  - trigger: webhook
    webhook_id: KEY
    local_only: true
    allowed_methods: [POST]
actions:
  - action: SERVICE
    data:
      title: "Horómetro · Mantenimiento"
      message: "{{ trigger.json.message }}"
      data:
        push:
          sound: default
        tag: "{{ trigger.json.id }}"
mode: queued
""".replace('KEY',key).replace('SERVICE',service)
    (BASE/'automatizacion.yaml').write_text(yaml,encoding='utf-8')
    cfg={'url':host+'/api/webhook/'+key}
    save(file,cfg)
    print('Se creo automatizacion.yaml en esta carpeta. Copielo en Home Assistant y guarde la automatizacion.')
    input('Cuando este guardada pulse Enter: ')
    return cfg
def main():
    cfg=setup()
    statefile=BASE/'ultima_entrega.json'
    seen=read(statefile) if statefile.exists() else None
    if input('Enviar aviso de PRUEBA al iPhone? [s/N] ').strip().lower()=='s':
        fetch(cfg['url'], {'id':'horometro-prueba','message':'Prueba de conexión desde el PC. No es un aviso de mantenimiento.'})
        print('Prueba enviada al servidor. Confirme la recepcion en el iPhone.')
    print('Deje abierta esta ventana, el panel USB y Home Assistant. Ctrl+C para salir.')
    last_msg=''
    while True:
        try:
            state=json.loads(fetch(PANEL))
            if not state['connected']:
                raise ValueError('Panel sin conexion USB')
            events=state['events']
            if seen is None:
                seen=[e['id'] for e in events][-200:]
                save(statefile,seen)
            for e in events:
                if e['id'] in seen: continue
                fetch(cfg['url'],{'id':e['id'],'message':e['message']})
                seen=(seen+[e['id']])[-200:]
                save(statefile,seen)
                print('Aviso enviado al servidor:',e['hours'],'h',flush=True)
            msg='Conectado. Esperando nuevos umbrales.'
        except (OSError, ValueError, KeyError) as exc:
            msg='Esperando el panel o el servidor: '+str(exc)
        if msg!=last_msg:
            print(msg,flush=True)
            last_msg=msg
        time.sleep(1)
if __name__=='__main__':
    try: main()
    except KeyboardInterrupt: pass
