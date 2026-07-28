#!/usr/bin/env python3
"""Cliente Wiimote para OperaCore (modo IoT), Linux y Windows.

Ejemplo: python wiimote_sensor.py --url http://127.0.0.1:8000 --maquina MAQ001
La máquina debe estar previamente en modo ``iot``.
"""
import argparse
import math
import platform
import sys
import time

import requests

try:
    import evdev
    from evdev import ecodes, ff
except Exception:
    evdev = ecodes = ff = None
try:
    import hid
except Exception:
    hid = None

NEUTRO, ESCALA = 512, 204.0
DELTA_GOLPE, COOLDOWN_SEG = 1.5, 2.0
BTN_A, BTN_B, BTN_HOME = "A", "B", "HOME"


def acc_a_g(x, y, z):
    ax, ay, az = ((v - NEUTRO) / ESCALA for v in (x, y, z))
    return ax, ay, az, math.sqrt(ax * ax + ay * ay + az * az)


def vibracion(x, y, z):
    return round(max(0.0, acc_a_g(x, y, z)[3] - 1.0), 3)


class DetectorGolpe:
    def __init__(self, delta, cooldown):
        self.delta, self.cooldown = delta, cooldown
        self.anterior, self.ultimo = 1.0, 0.0

    def evaluar(self, x, y, z):
        magnitud = acc_a_g(x, y, z)[3]
        cambio, ahora = abs(magnitud - self.anterior), time.time()
        self.anterior = magnitud
        if cambio >= self.delta and ahora - self.ultimo >= self.cooldown:
            self.ultimo = ahora
            return True, cambio, magnitud
        return False, cambio, magnitud


class ClienteCMMS:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def maquina(self, codigo):
        try:
            respuesta = self.session.get(f"{self.base_url}/api/monitoreo/maquinas/", timeout=5)
            respuesta.raise_for_status()
            return next((m for m in respuesta.json() if m["codigo"] == codigo), None)
        except requests.RequestException as error:
            print(f"[ERROR] No se pudo consultar máquinas: {error}")
            return None

    def maquina_iot_activa(self):
        """Pregunta al backend cuál es la única máquina en modo iot ahora
        mismo. El backend garantiza que nunca hay más de una a la vez."""
        try:
            respuesta = self.session.get(f"{self.base_url}/api/monitoreo/maquinas/iot-activa/", timeout=5)
            respuesta.raise_for_status()
            return respuesta.json().get("codigo")
        except requests.RequestException as error:
            print(f"[ERROR] No se pudo consultar la máquina iot activa: {error}")
            return None

    def lectura(self, codigo, valor, golpe=False):
        try:
            respuesta = self.session.post(
                f"{self.base_url}/api/monitoreo/lecturas/",
                json={"maquina": codigo, "origen": "iot", "vibracion": valor, "golpe": golpe, "temperatura": None},
                timeout=3,
            )
            if respuesta.status_code != 201:
                print(f"[ERROR] lectura: HTTP {respuesta.status_code} {respuesta.text[:800]}")
            return respuesta.status_code == 201
        except requests.RequestException as error:
            print(f"[ERROR] lectura: {error}")
            return False

    def reparar(self, codigo):
        try:
            respuesta = self.session.post(
                f"{self.base_url}/api/monitoreo/maquinas/{codigo}/reparar-iot/", timeout=3
            )
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.RequestException as error:
            print(f"[ERROR] reparar: {error}")
            return None


class LinuxWiimote:
    nombre = "Linux evdev"

    def __init__(self, acelerometro, botones):
        self.acelerometro, self.botones = acelerometro, botones
        self.x = self.y = self.z = NEUTRO
        self.ultimo = set()

    @classmethod
    def encontrar(cls):
        if evdev is None:
            raise RuntimeError("Instala python-evdev.")
        dispositivos = [evdev.InputDevice(p) for p in evdev.list_devices()]
        acelerometro = next((d for d in dispositivos if "Nintendo Wii Remote Accelerometer" in d.name), None)
        botones = next((d for d in dispositivos if d.name == "Nintendo Wii Remote"), None)
        return cls(acelerometro, botones) if acelerometro and botones else None

    def iniciar(self):
        # En versiones recientes de python-evdev los dispositivos ya se abren
        # en modo no bloqueante por defecto; set_blocking() fue removido.
        for dispositivo in (self.acelerometro, self.botones):
            if hasattr(dispositivo, "set_blocking"):
                dispositivo.set_blocking(False)

    def leer(self):
        try:
            for evento in self.acelerometro.read():
                if evento.type == ecodes.EV_ABS:
                    if evento.code in (ecodes.ABS_X, ecodes.ABS_RX): self.x = evento.value
                    if evento.code in (ecodes.ABS_Y, ecodes.ABS_RY): self.y = evento.value
                    if evento.code in (ecodes.ABS_Z, ecodes.ABS_RZ): self.z = evento.value
        except BlockingIOError:
            pass
        actual = set()
        try:
            for evento in self.botones.read():
                if evento.type == ecodes.EV_KEY and evento.value:
                    if evento.code in (ecodes.KEY_ENTER, ecodes.BTN_SOUTH): actual.add(BTN_A)
                    elif evento.code in (ecodes.KEY_SPACE, ecodes.BTN_THUMBR): actual.add(BTN_B)
                    elif evento.code in (ecodes.KEY_ESC, ecodes.BTN_MODE): actual.add(BTN_HOME)
        except BlockingIOError:
            pass
        nuevos, self.ultimo = actual - self.ultimo, actual
        return self.x, self.y, self.z, nuevos

    def rumble(self, segundos):
        """Rumble real vía force-feedback de evdev, sobre el mismo dispositivo
        de botones (el driver hid-wiimote del kernel expone FF_RUMBLE ahí)."""
        if ff is None:
            return None
        try:
            efecto = ff.Effect(
                ecodes.FF_RUMBLE, -1, 0,
                ff.Trigger(0, 0),
                ff.Replay(int(segundos * 1000), 0),
                ff.EffectType(ff_rumble_effect=ff.Rumble(strong_magnitude=0xFFFF, weak_magnitude=0xFFFF)),
            )
            effect_id = self.botones.upload_effect(efecto)
            self.botones.write(ecodes.EV_FF, effect_id, 1)
            time.sleep(segundos)
            self.botones.erase_effect(effect_id)
        except Exception as error:
            print(f"[WARN] No se pudo activar el rumble: {error}")

    def cerrar(self):
        self.acelerometro.close(); self.botones.close()


class WindowsWiimote:
    nombre, VID, PIDS = "Windows HID", 0x057E, {0x0306, 0x0330}
    MAPA = {0x0004: BTN_B, 0x0008: BTN_A, 0x0080: BTN_HOME}

    def __init__(self, dispositivo):
        self.dispositivo, self.x, self.y, self.z, self.ultimo = dispositivo, NEUTRO, NEUTRO, NEUTRO, set()

    @classmethod
    def encontrar(cls):
        if hid is None:
            raise RuntimeError("Instala hidapi: py -m pip install hidapi requests")
        info = next((d for d in hid.enumerate() if d["vendor_id"] == cls.VID and d["product_id"] in cls.PIDS), None)
        if not info: return None
        dispositivo = hid.device(); dispositivo.open_path(info["path"]); dispositivo.set_nonblocking(1)
        dispositivo.write(bytes([0x12, 0x04, 0x31] + [0] * 19))
        return cls(dispositivo)

    def iniciar(self): pass
    def cerrar(self): self.dispositivo.close()
    def rumble(self, segundos):
        self.dispositivo.write(bytes([0x11, 0x01] + [0] * 20)); time.sleep(segundos)
        self.dispositivo.write(bytes([0x11, 0x00] + [0] * 20))

    def leer(self):
        datos = self.dispositivo.read(32)
        if datos and datos[0] in (0x31, 0x33) and len(datos) >= 6:
            mascara = (datos[1] << 8) | datos[2]
            self.x, self.y, self.z = datos[3] * 4, datos[4] * 4, datos[5] * 4
            actual = {nombre for bit, nombre in self.MAPA.items() if mascara & bit}
            nuevos, self.ultimo = actual - self.ultimo, actual
            return self.x, self.y, self.z, nuevos
        return self.x, self.y, self.z, set()


def correr(url, codigo, intervalo, delta, cooldown, plataforma=None):
    cliente, detector = ClienteCMMS(url), DetectorGolpe(delta, cooldown)

    if not codigo:
        codigo = cliente.maquina_iot_activa()
        if not codigo:
            sys.exit("[ERROR] Ninguna máquina está en modo IoT ahora mismo. Actívalo desde el panel antes de correr el script.")
        print(f"[INFO] Vinculado automáticamente a la máquina en modo IoT: {codigo}")

    maquina = cliente.maquina(codigo)
    if not maquina:
        sys.exit(f"[ERROR] No existe la máquina {codigo}.")
    if maquina["modo_monitoreo"] != "iot":
        sys.exit(f"[ERROR] {codigo} no está en modo IoT.")
    clase = WindowsWiimote if (plataforma or platform.system()).lower().startswith("win") else LinuxWiimote
    wiimote = clase.encontrar()
    if not wiimote: sys.exit("[ERROR] No se encontró el Wiimote por Bluetooth.")
    wiimote.iniciar()
    print(f"OK {wiimote.nombre}; máquina [{codigo}] {maquina['nombre']}")
    print("Golpe=sensor | A=reparar | B=pausar | HOME=salir")

    TIEMPO_SIN_CAMBIO_MAX = 5.0  # seg. sin variación => se asume dormido/desconectado
    pausa, ultimo = False, 0.0
    valor_anterior, valor_desde = None, time.time()

    try:
        while True:
            x, y, z, botones = wiimote.leer()
            if BTN_HOME in botones: break
            if BTN_B in botones:
                pausa = not pausa; print("Pausa" if pausa else "Reanudado")
            if BTN_A in botones:
                resultado = cliente.reparar(codigo)
                print(f"Reparación: {resultado if resultado else 'error'}")
            ahora = time.time()
            actual = (x, y, z)
            if actual != valor_anterior:
                valor_anterior, valor_desde = actual, ahora
            sin_datos = (ahora - valor_desde) >= TIEMPO_SIN_CAMBIO_MAX

            if not pausa:
                golpe, cambio, mag = detector.evaluar(x, y, z)
                if sin_datos:
                    if ahora - ultimo >= intervalo:
                        print(f"[WARN] Sensor sin cambios hace {ahora - valor_desde:.1f}s; no se envía lectura (¿Wiimote dormido/desconectado?)")
                        ultimo = ahora
                elif golpe or ahora - ultimo >= intervalo:
                    ok = cliente.lectura(codigo, vibracion(x, y, z), golpe)
                    etiqueta = "GOLPE" if golpe else "OK"
                    resultado_envio = "enviado" if ok else "falló"
                    print(f"{etiqueta} mag={mag:.2f} delta={cambio:.2f} {resultado_envio}")
                    if golpe:
                        wiimote.rumble(0.25)
                    ultimo = ahora
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        wiimote.cerrar()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--maquina", required=False, default=None,
                         help="Código de la máquina. Si se omite, usa la única máquina que esté en modo iot.")
    parser.add_argument("--intervalo", type=float, default=0.5)
    parser.add_argument("--delta", type=float, default=DELTA_GOLPE)
    parser.add_argument("--cooldown", type=float, default=COOLDOWN_SEG)
    parser.add_argument("--plataforma", choices=["Linux", "Windows"])
    args = parser.parse_args()
    correr(args.url, args.maquina, args.intervalo, args.delta, args.cooldown, args.plataforma)