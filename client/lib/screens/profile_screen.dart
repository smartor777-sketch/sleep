import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class ProfileScreen extends StatefulWidget {
  final String email;
  final String aboutMe;
  final int totalDreams;
  final int totalAnalyses;
  final int streak;
  final Map<String, int> dreamsPerDay;
  final bool isDarkMode;                 // текущий режим
  final VoidCallback toggleTheme;        // функция смены темы
  final Color accentColor;
  final Function(Color) setAccentColor;

  const ProfileScreen({
    super.key,
    required this.email,
    required this.aboutMe,
    required this.totalDreams,
    required this.totalAnalyses,
    required this.streak,
    required this.dreamsPerDay,
    required this.isDarkMode,
    required this.toggleTheme,
    required this.accentColor,
    required this.setAccentColor,
  });

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late bool _isDarkMode;
  late Color _accentColor;
  late TextEditingController _aboutController;
  String _aboutText = '';

  @override
  void initState() {
    super.initState();
    _isDarkMode = widget.isDarkMode;
    _accentColor = widget.accentColor;
    _aboutText = widget.aboutMe;
    _aboutController = TextEditingController(text: _aboutText);
  }

  @override
  void didUpdateWidget(covariant ProfileScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.isDarkMode != widget.isDarkMode) {
      _isDarkMode = widget.isDarkMode;
    }
    if (oldWidget.accentColor != widget.accentColor) {
      _accentColor = widget.accentColor;
    }
    if (oldWidget.aboutMe != widget.aboutMe && _aboutText != widget.aboutMe) {
      _aboutText = widget.aboutMe;
      _aboutController.text = _aboutText;
    }
  }

  @override
  void dispose() {
    _aboutController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Профиль')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Email
            Text(
              widget.email,
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),

            // About Me
            TextField(
              controller: _aboutController,
              maxLines: null,
              decoration: InputDecoration(
                labelText: 'Обо мне',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(
                    color: Theme.of(context).colorScheme.outline.withOpacity(0.5),
                    width: 2,
                  ),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(
                    color: _accentColor,
                    width: 2,
                  ),
                ),
              ),
              onChanged: (value) {
                setState(() {
                  _aboutText = value;
                });
              },
            ),
            const SizedBox(height: 32),

            // Статистика
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildStatCard('Всего снов', widget.totalDreams.toString(), Colors.deepPurple),
                _buildStatCard('Всего анализов', widget.totalAnalyses.toString(), Colors.orange),
                _buildStatCard('Streak', widget.streak.toString(), Colors.green),
              ],
            ),
            const SizedBox(height: 32),

            // График снов по дням
            const Text(
              'Сны по дням недели',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            SizedBox(
              height: 200,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  maxY: (widget.dreamsPerDay.values.isEmpty
                          ? 1
                          : widget.dreamsPerDay.values.reduce((a,b) => a>b?a:b))
                      .toDouble() + 1,
                  titlesData: FlTitlesData(
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: true, reservedSize: 32),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          final days = widget.dreamsPerDay.keys.toList();
                          if (value.toInt() >= 0 && value.toInt() < days.length) {
                            return Text(days[value.toInt()]);
                          }
                          return const Text('');
                        },
                        reservedSize: 32,
                      ),
                    ),
                  ),
                  barGroups: widget.dreamsPerDay.entries.mapIndexed((index, entry) {
                    return BarChartGroupData(
                      x: index,
                      barRods: [
                        BarChartRodData(
                          toY: entry.value.toDouble(),
                          color: _accentColor,
                        )
                      ],
                    );
                  }).toList(),
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text('Выберите цвет акцента:', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                Colors.deepPurple,
                Colors.teal,
                Colors.orange,
                Colors.pink,
                Colors.lightBlue,
              ].map((color) {
                return GestureDetector(
                  onTap: () {
                    widget.setAccentColor(color);
                    setState(() {
                      _accentColor = color;
                    });
                  },
                  child: CircleAvatar(
                    backgroundColor: color,
                    radius: 20,
                    child: color == _accentColor
                        ? const Icon(Icons.check, color: Colors.white)
                        : null,
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 32),
            // Тёмная тема
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Темная тема', style: TextStyle(fontSize: 16)),
                Switch(
                  value: _isDarkMode,
                  onChanged: (_) {
                    widget.toggleTheme();
                    setState(() {
                      _isDarkMode = !_isDarkMode;
                    });
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard(String title, String value, Color color) {
    return Expanded(
      child: Card(
        elevation: 3,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
              const SizedBox(height: 4),
              Text(title, style: const TextStyle(fontSize: 14)),
            ],
          ),
        ),
      ),
    );
  }
}

// Extension для индексированной map
extension IterableExtensions<E> on Iterable<E> {
  Iterable<T> mapIndexed<T>(T Function(int index, E item) f) sync* {
    var i = 0;
    for (final e in this) {
      yield f(i++, e);
    }
  }
}