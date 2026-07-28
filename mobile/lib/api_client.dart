import 'dart:convert';
import 'package:http/http.dart' as http;

/// Modelo liviano de una máquina, tal como la devuelve
/// MaquinaListAPIView / CrearMaquinaAPIView en apps/monitoreo/views.py.
class Maquina {
  final String codigo;
  final String nombre;
  final String? linea;
  final String? estadoMaquina;
  String modoMonitoreo; // "manual" | "simulado" | "iot" (se actualiza local)
  final double umbralVibracion;
  final bool requiereRevisionPreventiva;

  Maquina({
    required this.codigo,
    required this.nombre,
    this.linea,
    this.estadoMaquina,
    required this.modoMonitoreo,
    required this.umbralVibracion,
    required this.requiereRevisionPreventiva,
  });

  factory Maquina.fromJson(Map<String, dynamic> j) => Maquina(
        codigo: j['codigo'] as String,
        nombre: j['nombre'] as String,
        linea: j['linea'] as String?,
        estadoMaquina: j['estado_maquina'] as String?,
        modoMonitoreo: j['modo_monitoreo'] as String? ?? 'manual',
        umbralVibracion: (j['umbral_vibracion'] as num?)?.toDouble() ?? 4.0,
        requiereRevisionPreventiva:
            j['requiere_revision_preventiva'] as bool? ?? false,
      );
}

/// Habla con la misma API REST que usa wiimote_sensor.py, bajo
/// /api/monitoreo/ (ver apps/monitoreo/urls.py del backend `api`).
class ApiClient {
  ApiClient(String baseUrl) : baseUrl = baseUrl.replaceAll(RegExp(r'/+$'), '');

  final String baseUrl;
  static const _timeout = Duration(seconds: 5);

  Uri _u(String path) => Uri.parse('$baseUrl$path');

  Map<String, dynamic>? _decode(http.Response r) {
    try {
      return jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  // ─── Ping / diagnóstico ─────────────────────────────────────────────
  Future<bool> ping() async {
    try {
      final r =
          await http.get(_u('/api/monitoreo/maquinas/')).timeout(_timeout);
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // ─── Máquinas ───────────────────────────────────────────────────────
  Future<List<Maquina>> listarMaquinas() async {
    try {
      final r =
          await http.get(_u('/api/monitoreo/maquinas/')).timeout(_timeout);
      if (r.statusCode != 200) return [];
      final data = jsonDecode(utf8.decode(r.bodyBytes)) as List;
      return data
          .map((e) => Maquina.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  /// Código de la máquina actualmente en modo iot (puede estar vinculada
  /// por el Wiimote o por otro celular; solo hay una a la vez).
  Future<String?> maquinaIotActiva() async {
    try {
      final r = await http
          .get(_u('/api/monitoreo/maquinas/iot-activa/'))
          .timeout(_timeout);
      if (r.statusCode != 200) return null;
      return _decode(r)?['codigo'] as String?;
    } catch (_) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> _cambiarModo(String codigo, String modo) async {
    try {
      final r = await http
          .patch(
            _u('/api/monitoreo/maquinas/$codigo/modo/'),
            headers: const {'Content-Type': 'application/json'},
            body: jsonEncode({'modo_monitoreo': modo}),
          )
          .timeout(_timeout);
      if (r.statusCode != 200) return null;
      return _decode(r);
    } catch (_) {
      return null;
    }
  }

  /// Vincula el celular a [codigo] (pone modo_monitoreo="iot").
  /// El backend libera automáticamente cualquier otra máquina que
  /// estuviera en iot (respuesta trae "maquina_iot_liberada").
  Future<Map<String, dynamic>?> vincular(String codigo) =>
      _cambiarModo(codigo, 'iot');

  /// Desvincula: regresa la máquina a modo manual.
  Future<Map<String, dynamic>?> desvincular(String codigo) =>
      _cambiarModo(codigo, 'manual');

  // ─── Lecturas ───────────────────────────────────────────────────────
  Future<Map<String, dynamic>?> enviarLectura({
    required String codigoMaquina,
    required double vibracion,
    bool golpe = false,
  }) async {
    try {
      final r = await http
          .post(
            _u('/api/monitoreo/lecturas/'),
            headers: const {'Content-Type': 'application/json'},
            body: jsonEncode({
              'maquina': codigoMaquina,
              'origen': 'iot',
              'vibracion': vibracion,
              'golpe': golpe,
              'temperatura': null,
            }),
          )
          .timeout(_timeout);
      if (r.statusCode != 201) return null;
      return _decode(r);
    } catch (_) {
      return null;
    }
  }

  // ─── Reparar (equivalente al botón A del Wiimote) ──────────────────
  Future<Map<String, dynamic>?> reparar(String codigo) async {
    try {
      final r = await http
          .post(_u('/api/monitoreo/maquinas/$codigo/reparar-iot/'))
          .timeout(_timeout);
      if (r.statusCode != 200) return null;
      return _decode(r);
    } catch (_) {
      return null;
    }
  }

  // ─── Estado (falla activa / revisión preventiva) ───────────────────
  Future<Map<String, dynamic>?> estado(String codigo) async {
    try {
      final r = await http
          .get(_u('/api/monitoreo/maquinas/$codigo/estado/'))
          .timeout(_timeout);
      if (r.statusCode != 200) return null;
      return _decode(r);
    } catch (_) {
      return null;
    }
  }
}
