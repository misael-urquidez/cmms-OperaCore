import 'dart:math';

/// Gravedad estándar en m/s². El acelerómetro del celular (sensors_plus)
/// reporta en m/s² incluyendo gravedad; el Wiimote reportaba 0-1023 con
/// NEUTRO=512. Aquí convertimos m/s² -> "g" para que la lógica sea idéntica
/// a la del script del Wiimote (acc_a_g / acc_a_vibracion / acc_a_inclinacion).
const double kGravedad = 9.80665;

class LecturaG {
  final double ax, ay, az, magnitud;
  const LecturaG(this.ax, this.ay, this.az, this.magnitud);
}

/// Convierte x,y,z en m/s² a "g" y calcula la magnitud del vector,
/// igual que acc_a_g() en wiimote_sensor.py.
LecturaG accAG(double x, double y, double z) {
  final ax = x / kGravedad;
  final ay = y / kGravedad;
  final az = z / kGravedad;
  final mag = sqrt(ax * ax + ay * ay + az * az);
  return LecturaG(ax, ay, az, mag);
}

/// "Vibración" = cuánto se aleja la magnitud de 1g (reposo), igual que
/// acc_a_vibracion() en wiimote_sensor.py.
double accAVibracion(LecturaG g) {
  return max(0.0, g.magnitud - 1.0);
}

/// Ángulo (en grados) entre el eje Z del teléfono y la gravedad, igual que
/// acc_a_inclinacion() en wiimote_sensor.py.
double accAInclinacion(LecturaG g) {
  if (g.magnitud == 0) return 0.0;
  final cosTheta = (g.az / g.magnitud).clamp(-1.0, 1.0);
  return acos(cosTheta) * 180 / pi;
}

class ResultadoGolpe {
  final bool golpe;
  final double delta;
  final double magnitud;
  const ResultadoGolpe(this.golpe, this.delta, this.magnitud);
}

/// Puerto de DetectorGolpe: detecta un cambio brusco de magnitud (un golpe o
/// sacudida) con un "cooldown" para no disparar fallas repetidas.
class DetectorGolpe {
  DetectorGolpe({this.delta = 1.5, this.cooldown = const Duration(seconds: 2)});

  final double delta;
  final Duration cooldown;

  double _magPrev = 1.0;
  DateTime _ultimo = DateTime.fromMillisecondsSinceEpoch(0);

  ResultadoGolpe evaluar(double magnitud) {
    final d = (magnitud - _magPrev).abs();
    _magPrev = magnitud;
    final ahora = DateTime.now();
    if (d >= delta && ahora.difference(_ultimo) >= cooldown) {
      _ultimo = ahora;
      return ResultadoGolpe(true, d, magnitud);
    }
    return ResultadoGolpe(false, d, magnitud);
  }
}
