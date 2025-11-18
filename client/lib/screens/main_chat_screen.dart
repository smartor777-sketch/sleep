import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../widgets/message_bubble.dart';
import '../widgets/message_menu.dart';
import '../models/dream.dart';
import '../models/user_profile.dart';
import 'profile_screen.dart';
import 'analysis_chat_screen.dart';

class MainChatScreen extends StatefulWidget {
  final UserProfile userProfile;
  final bool isDarkMode;
  final VoidCallback toggleTheme;
  final Color accentColor;
  final Function(Color) setAccentColor;

  const MainChatScreen({
    super.key,
    required this.userProfile,
    required this.isDarkMode,
    required this.toggleTheme,
    required this.accentColor,
    required this.setAccentColor,
  });


  @override
  State<MainChatScreen> createState() => _MainChatScreenState();
}

class _MainChatScreenState extends State<MainChatScreen> {
  final List<Dream> _dreams = []; // список объектов Dream
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  Dream? _editingDream;
  bool _showSearch = false;
  String _searchQuery = '';
  DateTime? _selectedDate;

  // Добавляем сон или редактируем существующий
  void _sendMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() {
      Dream newDream;
      if (_editingDream != null) {
        final index = _dreams.indexOf(_editingDream!);
        _dreams[index] = _editingDream!.copyWith(content: text);
        newDream = _dreams[index];
        _editingDream = null;
      } else {
        newDream = Dream(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          content: text,
        );
        _dreams.add(newDream);

        // обновляем статистику пользователя
        widget.userProfile.totalDreams = _dreams.length;

        final weekday = [
          'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'
        ][newDream.createdAt.weekday - 1];
        widget.userProfile.weekdayStats[weekday] =
            (widget.userProfile.weekdayStats[weekday] ?? 0) + 1;
      }

      _controller.clear();
    });
  }

  // Фильтруем сны по поиску и дате
  List<Dream> get _filteredDreams {
    return _dreams.where((dream) {
      final matchesSearch = _searchQuery.isEmpty ||
          dream.content.toLowerCase().contains(_searchQuery.toLowerCase());
      final matchesDate = _selectedDate == null ||
          (dream.createdAt.year == _selectedDate!.year &&
           dream.createdAt.month == _selectedDate!.month &&
           dream.createdAt.day == _selectedDate!.day);
      return matchesSearch && matchesDate;
    }).toList();
  }

  late Color _accentColor;

  @override
  void initState() {
    super.initState();
    _accentColor = widget.accentColor;
  }

  @override
  void didUpdateWidget(covariant MainChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.accentColor != widget.accentColor) {
      setState(() {
        _accentColor = widget.accentColor;
      });
    }
  }

  void _handleAccentColorChange(Color color) {
    if (_accentColor == color) return;
    setState(() {
      _accentColor = color;
    });
    widget.setAccentColor(color);
  }

  void _openMessageMenu(Dream dream, Offset globalPosition) {
    final overlay = Overlay.of(context).context.findRenderObject() as RenderBox?;
    final overlayPosition =
        overlay?.globalToLocal(globalPosition) ?? globalPosition;

    MessageMenu.show(
      context,
      position: overlayPosition,
      onCopy: () {
        Clipboard.setData(ClipboardData(text: dream.content));
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Сон скопирован')),
        );
      },
      onEdit: () {
        setState(() {
          _editingDream = dream;
          _controller.text = dream.content;
        });
      },
      onDelete: () {
        setState(() {
          _dreams.remove(dream);
        });
      },
      onAnalyze: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => AnalysisChatScreen(
              dream: dream,
              accentColor: _accentColor,
              setAccentColor: _handleAccentColorChange,
            ),
          ),
        );
      },
    );
  }

  Future<void> _openCalendarDialog() async {
    final initialDate = _selectedDate ?? DateTime.now();
    final date = await showGeneralDialog<DateTime>(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'Calendar',
      barrierColor: Colors.black.withOpacity(0.2),
      pageBuilder: (dialogContext, animation, secondaryAnimation) {
        return Material(
          color: Colors.transparent,
          child: Stack(
            children: [
              Positioned.fill(
                child: GestureDetector(
                  onTap: () => Navigator.of(dialogContext).pop(),
                  child: BackdropFilter(
                    filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
                    child: Container(color: Colors.black.withOpacity(0.05)),
                  ),
                ),
              ),
              Center(
                child: DatePickerDialog(
                  initialDate: initialDate.isBefore(DateTime(2020))
                      ? DateTime(2020)
                      : initialDate,
                  firstDate: DateTime(2020),
                  lastDate: DateTime.now(),
                ),
              ),
            ],
          ),
        );
      },
    );

    if (date != null) {
      setState(() {
        _selectedDate = date;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('JungAI'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              setState(() {
                _showSearch = !_showSearch;
                if (!_showSearch) _searchQuery = '';
              });
            },
          ),
          IconButton(
            icon: const Icon(Icons.person),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => ProfileScreen(
                    email: widget.userProfile.email,
                    aboutMe: widget.userProfile.aboutMe ?? '',
                    totalDreams: 42,       // временные данные
                    totalAnalyses: 10,     // временные данные
                    streak: 5,             // временные данные
                    dreamsPerDay: {
                      'Пн': 2,
                      'Вт': 3,
                      'Ср': 1,
                      'Чт': 0,
                      'Пт': 4,
                      'Сб': 2,
                      'Вс': 1,
                    },
                    isDarkMode: widget.isDarkMode,
                    toggleTheme: widget.toggleTheme,
                    accentColor: _accentColor,
                    setAccentColor: _handleAccentColorChange,
                  ),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.calendar_today),
            onPressed: _openCalendarDialog,
          ),
        ],
      ),
      body: Column(
        children: [
          // Строка поиска
          if (_showSearch)
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: TextField(
                autofocus: true,
                decoration: InputDecoration(
                  hintText: 'Поиск снов...',
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
                  setState(() => _searchQuery = value);
                },
              ),
            ),
          // Список сообщений
          Expanded(
            child: ListView.builder(
              reverse: true, // новые сообщения снизу
              controller: _scrollController,
              itemCount: _filteredDreams.length,
              itemBuilder: (context, index) {
                final dream = _filteredDreams[_filteredDreams.length - 1 - index];
                return MessageBubble(
                  message: dream.content,
                  isUserMessage: true,
                  accentColor: _accentColor,
                  onLongPressStart: (details) =>
                      _openMessageMenu(dream, details.globalPosition),
                );
              },
            ),
          ),
          // Поле ввода
          Container(
            margin: const EdgeInsets.all(12), // отступ от краёв экрана
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Theme.of(context).brightness == Brightness.dark
                  ? Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.4)
                  : Theme.of(context).colorScheme.surfaceVariant,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
              ),
            ),
            child: Row(
              children: [
                IconButton(
                  icon: Icon(Icons.mic, color: _accentColor),
                  onPressed: () {
                    // TODO: голосовой ввод
                  },
                ),

                Expanded(
                  child: TextField(
                    controller: _controller,
                    maxLines: null, // позволяет увеличивать высоту при наборе
                    decoration: InputDecoration(
                      hintText: _editingDream != null
                          ? 'Редактировать сон...'
                          : 'Напишите сон...',
                      border: InputBorder.none,
                    ),
                  ),
                ),

                const SizedBox(width: 8),

                Container(
                  decoration: BoxDecoration(
                    color: _accentColor,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.white),
                    onPressed: _sendMessage,
                  ),
                )
              ],
            ),
          )
        ],
      ),
    );
  }
}