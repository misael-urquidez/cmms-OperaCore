import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:vibration/vibration.dart';

import 'api_client.dart';
import 'sensor_logic.dart';

const _kPrefUltimaUrl = 'operacore_ultima_url';
const _kPrefPerfiles = 'operacore_perfiles';

void main() => runApp(const OperaCoreSensorApp());

class OperaCoreSensorApp extends StatelessWidget {
  const OperaCoreSensorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'OperaCore · Sensor IoT',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00897B),
          brightness: Brightness.dark,
        ),
      ),
      home: const SensorScreen(),
    );
  }
}

/// Perfil de servidor guardado (nombre + URL), para no tener que
/// escribir la IP cada vez que cambia (DHCP, otra planta, etc.).
class ServidorPerfil {
  final String nombre;
  final String url;
  const ServidorPerfil({required this.nombre, required this.url});

  factory ServidorPerfil.fromJson(Map<String, dynamic> j) =>
      ServidorPerfil(nombre: j['nombre'] as String, url: j['url'] as String);

  Map<String, dynamic> toJson() => {'nombre': nombre, 'url': url};
}

class SensorScreen extends StatefulWidget {
  const SensorScreen({super.key});

  @override
  State<SensorScreen> createState() => _SensorScreenState();
}

class _SensorScreenState extends State<SensorScreen>
    with SingleTickerProviderStateMixin {
  final _urlController = TextEditingController();

  ApiClient? _api;
  StreamSubscription<AccelerometerEvent>? _accelSub;
  Timer? _heartbeat;
  Timer? _pollEstado;
  final _detector =
      DetectorGolpe(delta: 1.5, cooldown: const Duration(seconds: 2));

  bool _conectando = false;
  bool _enviando = false;
  bool _pausado = false;
  bool _hasFalla = false;
  bool _requiereRevision = false;

  List<ServidorPerfil> _perfiles = [];
  List<Maquina> _maquinas = [];
  String? _lineaSeleccionada; // null = todas las líneas
  Maquina? _vinculada;
  String? _iotActivaEnServidor;

  LecturaG _ultimaG = const LecturaG(0, 0, 0, 0);
  double _ultimaVib = 0;
  double _ultimaInc = 0;
  String _estado = 'Sin conectar';
  int _lecturasSent = 0;

  late final AnimationController _golpeAnim;
  late final Animation<double> _golpeScale;

  @override
  void initState() {
    super.initState();
    _golpeAnim = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _golpeScale = Tween<double>(begin: 1.0, end: 1.25)
        .animate(CurvedAnimation(parent: _golpeAnim, curve: Curves.elasticOut));
    _cargarPrefs();
  }

  @override
  void dispose() {
    _accelSub?.cancel();
    _heartbeat?.cancel();
    _pollEstado?.cancel();
    _golpeAnim.dispose();
    super.dispose();
  }

  // ─── Líneas / filtro ────────────────────────────────────────────────
  List<String> get _lineasDisponibles {
    final set = <String>{};
    for (final m in _maquinas) {
      if (m.linea != null && m.linea!.isNotEmpty) set.add(m.linea!);
    }
    final lista = set.toList()..sort();
    return lista;
  }

  List<Maquina> get _maquinasFiltradas {
    if (_lineaSeleccionada == null) return _maquinas;
    return _maquinas.where((m) => m.linea == _lineaSeleccionada).toList();
  }

  // ─── Prefs / perfiles ───────────────────────────────────────────────
  Future<void> _cargarPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final ultima = prefs.getString(_kPrefUltimaUrl) ?? '';
    final raw = prefs.getStringList(_kPrefPerfiles) ?? [];
    final perfiles = raw
        .map((s) {
          try {
            return ServidorPerfil.fromJson(
                jsonDecode(s) as Map<String, dynamic>);
          } catch (_) {
            return null;
          }
        })
        .whereType<ServidorPerfil>()
        .toList();
    setState(() {
      _perfiles = perfiles;
      _urlController.text = ultima.isNotEmpty
          ? ultima
          : (perfiles.isNotEmpty
              ? perfiles.first.url
              : 'http://192.168.0.6:8000');
    });
  }

  Future<void> _guardarUltimaUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kPrefUltimaUrl, url);
  }

  Future<void> _guardarPerfilesEnDisco() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
      _kPrefPerfiles,
      _perfiles.map((p) => jsonEncode(p.toJson())).toList(),
    );
  }

  Future<void> _guardarPerfilActual() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) return;
    final nombre = await showDialog<String>(
      context: context,
      builder: (ctx) {
        final controller = TextEditingController();
        return AlertDialog(
          title: const Text('Guardar como perfil'),
          content: TextField(
            controller: controller,
            autofocus: true,
            decoration: const InputDecoration(
              labelText: 'Nombre',
              hintText: 'Ej. Compu de Misael',
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, controller.text.trim()),
              child: const Text('Guardar'),
            ),
          ],
        );
      },
    );
    if (nombre == null || nombre.isEmpty) return;
    setState(() {
      _perfiles.removeWhere((p) => p.nombre == nombre);
      _perfiles.insert(0, ServidorPerfil(nombre: nombre, url: url));
      if (_perfiles.length > 10) _perfiles = _perfiles.sublist(0, 10);
    });
    await _guardarPerfilesEnDisco();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Perfil "$nombre" guardado')),
      );
    }
  }

  Future<void> _borrarPerfil(ServidorPerfil p) async {
    setState(() => _perfiles.remove(p));
    await _guardarPerfilesEnDisco();
  }

  // ─── Feedback ───────────────────────────────────────────────────────
  void _feedback({bool error = false, bool ok = false}) {
    SystemSound.play(error ? SystemSoundType.alert : SystemSoundType.click);
    if (error) {
      HapticFeedback.vibrate();
    } else if (ok) {
      HapticFeedback.lightImpact();
    }
  }

  /// Vibración fuerte al detectar un golpe. Usa el paquete `vibration`
  /// (control de duración/amplitud real) y si el teléfono no lo soporta
  /// cae de vuelta a HapticFeedback.
  Future<void> _vibrarGolpe() async {
    try {
      final tieneVibrador = await Vibration.hasVibrator();
      if (tieneVibrador == true) {
        final tieneAmplitud = await Vibration.hasAmplitudeControl();
        if (tieneAmplitud == true) {
          Vibration.vibrate(duration: 400, amplitude: 255);
        } else {
          Vibration.vibrate(duration: 400);
        }
        return;
      }
    } catch (_) {
      // Sigue al fallback.
    }
    HapticFeedback.heavyImpact();
  }

  // ─── Conexión ───────────────────────────────────────────────────────
  Future<void> _conectar() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) return;
    setState(() {
      _conectando = true;
      _estado = 'Conectando con $url…';
      _maquinas = [];
      _lineaSeleccionada = null;
      _vinculada = null;
      _iotActivaEnServidor = null;
    });

    final api = ApiClient(url);
    final ok = await api.ping();
    if (!ok) {
      _feedback(error: true);
      setState(() {
        _conectando = false;
        _estado =
            'No se pudo conectar. Verifica la URL y que Django esté corriendo (0.0.0.0:8000).';
      });
      return;
    }

    final maquinas = await api.listarMaquinas();
    final iotActiva = await api.maquinaIotActiva();

    await _guardarUltimaUrl(url);
    _feedback(ok: true);

    setState(() {
      _api = api;
      _conectando = false;
      _maquinas = maquinas;
      _iotActivaEnServidor = iotActiva;
      if (iotActiva != null) {
        final existente = maquinas.where((m) => m.codigo == iotActiva);
        if (existente.isNotEmpty) {
          _vinculada = existente.first;
          _estado = 'Vinculado a "${_vinculada!.nombre}"';
          _iniciarPollEstado();
        }
      } else {
        _estado = maquinas.isEmpty
            ? 'Conectado. No hay máquinas registradas.'
            : 'Conectado. Filtra por línea y selecciona una máquina.';
      }
    });
  }

  // ─── Vincular / desvincular ─────────────────────────────────────────
  Future<void> _vincularMaquina(Maquina maquina) async {
    if (_api == null) return;
    setState(() => _estado = 'Vinculando con "${maquina.nombre}"…');
    final resultado = await _api!.vincular(maquina.codigo);
    if (resultado == null) {
      _feedback(error: true);
      setState(() => _estado = 'Error al vincular. Intenta de nuevo.');
      return;
    }
    _feedback(ok: true);
    final liberada = resultado['maquina_iot_liberada'] as String?;
    setState(() {
      maquina.modoMonitoreo = 'iot';
      for (final m in _maquinas) {
        if (m.codigo != maquina.codigo && m.modoMonitoreo == 'iot') {
          m.modoMonitoreo = 'manual';
        }
      }
      _vinculada = maquina;
      _iotActivaEnServidor = maquina.codigo;
      _hasFalla = false;
      _requiereRevision = maquina.requiereRevisionPreventiva;
      _estado = liberada != null
          ? 'Vinculado a "${maquina.nombre}" (se liberó $liberada)'
          : 'Vinculado a "${maquina.nombre}"';
    });
    _iniciarPollEstado();
  }

  Future<void> _desvincular() async {
    _detenerEnvio();
    _pollEstado?.cancel();
    if (_api != null && _vinculada != null) {
      await _api!.desvincular(_vinculada!.codigo);
    }
    setState(() {
      if (_vinculada != null) _vinculada!.modoMonitoreo = 'manual';
      _vinculada = null;
      _hasFalla = false;
      _requiereRevision = false;
      _estado = 'Desvinculado. Selecciona una máquina.';
    });
  }

  // ─── Poll de estado ─────────────────────────────────────────────────
  void _iniciarPollEstado() {
    _pollEstado?.cancel();
    _pollEstado = Timer.periodic(const Duration(seconds: 4), (_) async {
      if (_api == null || _vinculada == null) return;
      final e = await _api!.estado(_vinculada!.codigo);
      if (e == null || !mounted) return;
      setState(() {
        _hasFalla = e['falla_activa'] as bool? ?? false;
        _requiereRevision = e['requiere_revision_preventiva'] as bool? ?? false;
      });
    });
  }

  // ─── Envío de lecturas ──────────────────────────────────────────────
  void _iniciarEnvio() {
    if (_api == null || _vinculada == null) return;
    setState(() {
      _enviando = true;
      _pausado = false;
      _lecturasSent = 0;
    });

    _accelSub = accelerometerEventStream(
      samplingPeriod: SensorInterval.gameInterval,
    ).listen((evento) {
      final g = accAG(evento.x, evento.y, evento.z);
      final vib = accAVibracion(g);
      final inc = accAInclinacion(g);
      final resultado = _detector.evaluar(g.magnitud);

      setState(() {
        _ultimaG = g;
        _ultimaVib = vib;
        _ultimaInc = inc;
      });

      if (resultado.golpe && !_pausado) {
        _mandarLectura(vib, golpe: true);
        _onGolpe();
      }
    }, onError: (_) {
      setState(() =>
          _estado = '⚠ No se pudo leer el acelerómetro de este dispositivo');
    });

    _heartbeat = Timer.periodic(const Duration(milliseconds: 500), (_) {
      if (_pausado) return;
      _mandarLectura(_ultimaVib);
    });
  }

  void _onGolpe() {
    _vibrarGolpe();
    _golpeAnim.forward(from: 0);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: Colors.black),
              SizedBox(width: 8),
              Text('💥 Golpe detectado → lectura enviada',
                  style: TextStyle(
                      color: Colors.black, fontWeight: FontWeight.bold)),
            ],
          ),
          backgroundColor: Colors.orangeAccent,
          duration: Duration(seconds: 3),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  Future<void> _mandarLectura(double vib, {bool golpe = false}) async {
    if (_vinculada == null) return;
    final resultado = await _api!.enviarLectura(
      codigoMaquina: _vinculada!.codigo,
      vibracion: vib,
      golpe: golpe,
    );
    if (!mounted) return;
    setState(() {
      if (resultado != null) {
        _lecturasSent++;
        _estado = 'Enviando lecturas a "${_vinculada?.nombre}"';
        final reporte = resultado['reporte_automatico'];
        if (reporte != null) _hasFalla = true;
        _requiereRevision =
            resultado['requiere_revision_preventiva'] as bool? ??
                _requiereRevision;
      } else {
        _estado = '⚠ Error enviando lectura al servidor';
      }
    });
  }

  void _detenerEnvio() {
    _accelSub?.cancel();
    _heartbeat?.cancel();
    setState(() {
      _enviando = false;
      _estado = _vinculada != null
          ? 'Detenido. Vinculado a "${_vinculada!.nombre}"'
          : 'Detenido.';
    });
  }

  // ─── Reparar ────────────────────────────────────────────────────────
  Future<void> _reparar() async {
    if (_api == null || _vinculada == null) return;
    final resultado = await _api!.reparar(_vinculada!.codigo);
    if (!mounted) return;
    if (resultado == null) {
      _feedback(error: true);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Error de comunicación con el servidor')));
      return;
    }
    final reparado = resultado['resultado'] == 'reparado';
    if (reparado) {
      setState(() => _hasFalla = false);
      _feedback(ok: true);
      HapticFeedback.mediumImpact();
    }
    final msg = reparado
        ? '✔ Falla resuelta en ${resultado['maquina']}'
        : 'Sin fallas activas en esta máquina';
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: reparado ? Colors.green.shade700 : null,
      behavior: SnackBarBehavior.floating,
    ));
  }

  // ─── UI ─────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      backgroundColor: cs.surface,
      appBar: AppBar(
        title: const Text('OperaCore · Sensor IoT'),
        centerTitle: false,
        actions: [
          if (_vinculada != null)
            IconButton(
              icon: const Icon(Icons.link_off),
              tooltip: 'Desvincular máquina',
              onPressed: _desvincular,
            ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          _SectionCard(
            title: 'Servidor Django (api)',
            icon: Icons.dns_rounded,
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _urlController,
                        enabled: !_enviando,
                        decoration: const InputDecoration(
                          labelText: 'URL del backend',
                          hintText: 'http://192.168.0.6:8000',
                          border: OutlineInputBorder(),
                          isDense: true,
                        ),
                        keyboardType: TextInputType.url,
                        autocorrect: false,
                      ),
                    ),
                    const SizedBox(width: 8),
                    IconButton(
                      icon: const Icon(Icons.bookmark_add_outlined),
                      tooltip: 'Guardar como perfil',
                      onPressed: _enviando ? null : _guardarPerfilActual,
                    ),
                    if (_perfiles.isNotEmpty)
                      PopupMenuButton<ServidorPerfil>(
                        icon: const Icon(Icons.bookmark_outline),
                        tooltip: 'Perfiles guardados',
                        onSelected: (p) =>
                            setState(() => _urlController.text = p.url),
                        itemBuilder: (_) => _perfiles
                            .map((p) => PopupMenuItem(
                                  value: p,
                                  child: Row(
                                    children: [
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Text(p.nombre,
                                                style: const TextStyle(
                                                    fontWeight:
                                                        FontWeight.w600)),
                                            Text(p.url,
                                                style: const TextStyle(
                                                    fontSize: 11)),
                                          ],
                                        ),
                                      ),
                                      IconButton(
                                        icon: const Icon(Icons.close, size: 18),
                                        onPressed: () {
                                          Navigator.pop(context);
                                          _borrarPerfil(p);
                                        },
                                      ),
                                    ],
                                  ),
                                ))
                            .toList(),
                      ),
                  ],
                ),
                const SizedBox(height: 10),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: _conectando || _enviando ? null : _conectar,
                    icon: _conectando
                        ? const SizedBox.square(
                            dimension: 18,
                            child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.wifi),
                    label: Text(_conectando ? 'Conectando…' : 'Conectar'),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          _EstadoCard(
              estado: _estado,
              hasFalla: _hasFalla,
              requiereRevision: _requiereRevision),
          const SizedBox(height: 12),
          if (_api != null && _vinculada == null && _maquinas.isNotEmpty)
            _SectionCard(
              title: 'Máquinas',
              icon: Icons.precision_manufacturing_rounded,
              child: Column(
                children: [
                  DropdownButtonFormField<String?>(
                    initialValue: _lineaSeleccionada,
                    decoration: const InputDecoration(
                      labelText: 'Línea',
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                    items: [
                      const DropdownMenuItem<String?>(
                          value: null, child: Text('Todas las líneas')),
                      ..._lineasDisponibles.map(
                        (l) =>
                            DropdownMenuItem<String?>(value: l, child: Text(l)),
                      ),
                    ],
                    onChanged: (v) => setState(() => _lineaSeleccionada = v),
                  ),
                  const SizedBox(height: 10),
                  ..._maquinasFiltradas.map((m) {
                    final yaIot = m.modoMonitoreo == 'iot';
                    return ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: Icon(Icons.memory,
                          color: yaIot ? Colors.orangeAccent : null),
                      title: Text(m.nombre),
                      subtitle: Text(
                          '${m.codigo}${m.linea != null ? ' · ${m.linea}' : ''} · modo: ${m.modoMonitoreo}'),
                      trailing: FilledButton.tonal(
                        onPressed: () => _vincularMaquina(m),
                        child: Text(yaIot ? 'Tomar control' : 'Vincular'),
                      ),
                    );
                  }),
                  if (_maquinasFiltradas.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 8),
                      child: Text('No hay máquinas en esta línea.'),
                    ),
                ],
              ),
            ),
          if (_api != null && _vinculada == null && _maquinas.isNotEmpty)
            const SizedBox(height: 12),
          if (_vinculada != null) ...[
            _SectionCard(
              title: 'Controles',
              icon: Icons.gamepad_rounded,
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: FilledButton.icon(
                          onPressed: _enviando ? null : _iniciarEnvio,
                          icon: const Icon(Icons.sensors),
                          label: const Text('Iniciar'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _enviando ? _detenerEnvio : null,
                          icon: const Icon(Icons.stop_circle_outlined),
                          label: const Text('Detener'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _enviando
                              ? () => setState(() => _pausado = !_pausado)
                              : null,
                          icon: Icon(_pausado ? Icons.play_arrow : Icons.pause),
                          label: Text(_pausado ? 'Reanudar' : 'Pausar'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: FilledButton.tonalIcon(
                          onPressed: _reparar,
                          icon: const Icon(Icons.build_circle_outlined),
                          label: const Text('Reparar'),
                          style: _hasFalla
                              ? FilledButton.styleFrom(
                                  backgroundColor: Colors.orange.shade700)
                              : null,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            _SectionCard(
              title: 'Lecturas en vivo',
              icon: Icons.show_chart_rounded,
              trailing: _enviando
                  ? Text('$_lecturasSent enviadas',
                      style: TextStyle(
                          fontSize: 12,
                          color: Theme.of(context).colorScheme.primary))
                  : null,
              child: ScaleTransition(
                scale: _golpeScale,
                child: Column(
                  children: [
                    _MetricRow(
                        label: 'Magnitud',
                        value: '${_ultimaG.magnitud.toStringAsFixed(3)} g',
                        icon: Icons.vibration,
                        isHigh: _ultimaG.magnitud > 2.0),
                    const SizedBox(height: 6),
                    _MetricRow(
                        label: 'Vibración',
                        value: '${_ultimaVib.toStringAsFixed(3)} g',
                        icon: Icons.waves,
                        isHigh: _ultimaVib > _vinculada!.umbralVibracion),
                    const SizedBox(height: 6),
                    _MetricRow(
                        label: 'Inclinación',
                        value: '${_ultimaInc.toStringAsFixed(1)}°',
                        icon: Icons.screen_rotation,
                        isHigh: _ultimaInc > 45),
                    if (_pausado)
                      Padding(
                        padding: const EdgeInsets.only(top: 10),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.pause_circle,
                                size: 16, color: Colors.orange.shade300),
                            const SizedBox(width: 6),
                            Text('Envío pausado',
                                style: TextStyle(
                                    color: Colors.orange.shade300,
                                    fontStyle: FontStyle.italic)),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ─── Widgets auxiliares ─────────────────────────────────────────────────
class _SectionCard extends StatelessWidget {
  const _SectionCard(
      {required this.title,
      required this.icon,
      required this.child,
      this.trailing});
  final String title;
  final IconData icon;
  final Widget child;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: cs.outlineVariant.withOpacity(0.5))),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Icon(icon, size: 18, color: cs.primary),
              const SizedBox(width: 8),
              Text(title,
                  style: TextStyle(
                      fontWeight: FontWeight.w600, color: cs.primary)),
              if (trailing != null) ...[const Spacer(), trailing!],
            ]),
            const SizedBox(height: 14),
            child,
          ],
        ),
      ),
    );
  }
}

class _EstadoCard extends StatelessWidget {
  const _EstadoCard(
      {required this.estado,
      required this.hasFalla,
      required this.requiereRevision});
  final String estado;
  final bool hasFalla;
  final bool requiereRevision;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final color = hasFalla
        ? Colors.orange.shade700
        : estado.startsWith('⚠')
            ? Colors.red.shade700
            : cs.surfaceContainerHigh;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 400),
      curve: Curves.easeInOut,
      decoration:
          BoxDecoration(color: color, borderRadius: BorderRadius.circular(16)),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          Icon(
              hasFalla
                  ? Icons.warning_amber_rounded
                  : Icons.info_outline_rounded,
              color: hasFalla ? Colors.white : cs.onSurface.withOpacity(0.6)),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(estado,
                    style: TextStyle(
                        color: hasFalla ? Colors.white : cs.onSurface,
                        fontWeight:
                            hasFalla ? FontWeight.bold : FontWeight.normal)),
                if (requiereRevision)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text('Requiere revisión preventiva',
                        style: TextStyle(
                            fontSize: 12,
                            color: hasFalla
                                ? Colors.white70
                                : Colors.amber.shade300)),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricRow extends StatelessWidget {
  const _MetricRow(
      {required this.label,
      required this.value,
      required this.icon,
      this.isHigh = false});
  final String label;
  final String value;
  final IconData icon;
  final bool isHigh;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final accentColor = isHigh ? Colors.orangeAccent : cs.primary;
    return Row(
      children: [
        Icon(icon, size: 18, color: accentColor),
        const SizedBox(width: 10),
        Expanded(
            child: Text(label,
                style: TextStyle(color: cs.onSurface.withOpacity(0.7)))),
        Text(value,
            style: TextStyle(
                fontFamily: 'monospace',
                fontWeight: FontWeight.w600,
                color: isHigh ? Colors.orangeAccent : cs.onSurface)),
      ],
    );
  }
}
