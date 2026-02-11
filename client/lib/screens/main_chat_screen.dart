import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../l10n/app_localizations.dart';
import '../widgets/dream_card.dart';
import '../widgets/message_menu.dart';
import '../models/dream.dart';
import '../providers/auth_provider.dart';
import '../providers/dreams_provider.dart';
import '../providers/analysis_provider.dart';
import 'profile_screen.dart';
import 'analysis_chat_screen.dart';

class MainChatScreen extends StatefulWidget {
  final bool isDarkMode;
  final VoidCallback toggleTheme;
  final Color accentColor;
  final Function(Color) setAccentColor;
  final Function(Locale) setLocale;
  final double textScale;
  final Function(double) setTextScale;

  const MainChatScreen({
    super.key,
    required this.isDarkMode,
    required this.toggleTheme,
    required this.accentColor,
    required this.setAccentColor,
    required this.setLocale,
    required this.textScale,
    required this.setTextScale,
  });


  @override
  State<MainChatScreen> createState() => _MainChatScreenState();
}

class _MainChatScreenState extends State<MainChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  Dream? _editingDream;
  bool _showSearch = false;
  String _searchQuery = '';
  DateTime? _selectedDate;

  // Добавляем сон или редактируем существующий
  Future<void> _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    final provider = context.read<DreamsProvider>();
    final l10n = AppLocalizations.of(context)!;
    if (_editingDream != null) {
      final updated = await provider.updateDream(_editingDream!.id, text);
      if (updated == null) {
        _showError(l10n.dreamSaveError);
        return;
      }
      _editingDream = null;
      _controller.clear();
      return;
    }

    final created = await provider.createDream(text);
    if (created == null) {
      _showError(l10n.dreamSaveError);
      return;
    }
    _controller.clear();

    // stats handled on backend
  }

  // Фильтруем сны по поиску и дате
  List<Dream> _filterDreams(List<Dream> source) {
    return source.where((dream) {
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
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DreamsProvider>().loadDreams();
    });
  }

  @override
  void didUpdateWidget(covariant MainChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.accentColor != widget.accentColor) {
      setState(() {
        _accentColor = widget.accentColor;
      });
    }
    // user email handled via AuthProvider
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
          SnackBar(content: Text(AppLocalizations.of(context)!.dreamCopied)),
        );
      },
      onEdit: () {
        setState(() {
          _editingDream = dream;
          _controller.text = dream.content;
        });
      },
      onDelete: () {
        _deleteDream(dream);
      },
      onAnalyze: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => ChangeNotifierProvider(
              create: (_) => AnalysisProvider(context.read<AuthProvider>()),
              child: AnalysisChatScreen(
                dream: dream,
                accentColor: _accentColor,
                setAccentColor: _handleAccentColorChange,
              ),
            ),
          ),
        );
      },
    );
  }

  Future<void> _deleteDream(Dream dream) async {
    final ok = await context.read<DreamsProvider>().deleteDream(dream.id);
    if (!ok) _showError(AppLocalizations.of(context)!.dreamDeleteError);
  }

  Future<void> _search(String query) async {
    await context.read<DreamsProvider>().search(query);
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  String _mapDreamsError(int? code, String? message) {
    final l10n = AppLocalizations.of(context)!;
    if (code == 429) {
      return l10n.rateLimitError;
    }
    if (message == 'network_error') {
      return l10n.networkError;
    }
    return l10n.genericError;
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
      final formatted =
          '${date.year.toString().padLeft(4, '0')}-'
          '${date.month.toString().padLeft(2, '0')}-'
          '${date.day.toString().padLeft(2, '0')}';
      context.read<DreamsProvider>().loadDreams(date: formatted);
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
                if (!_showSearch) {
                  _searchQuery = '';
                  context.read<DreamsProvider>().search('');
                }
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
                    isDarkMode: widget.isDarkMode,
                    toggleTheme: widget.toggleTheme,
                    accentColor: _accentColor,
                    setAccentColor: _handleAccentColorChange,
                    setLocale: widget.setLocale,
                    textScale: widget.textScale,
                    setTextScale: widget.setTextScale,
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
                  hintText: AppLocalizations.of(context)!.searchHint,
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
                  _search(value);
                },
              ),
            ),
          // Список сообщений
          Expanded(
            child: Consumer<DreamsProvider>(
              builder: (context, provider, _) {
                if (provider.error != null) {
                  WidgetsBinding.instance.addPostFrameCallback((_) {
                    _showError(_mapDreamsError(provider.errorCode, provider.error));
                    provider.clearError();
                  });
                }
                if (provider.loading && provider.dreams.isEmpty) {
                  return const Center(child: CircularProgressIndicator());
                }
                final source = _searchQuery.isEmpty ? provider.dreams : provider.searchResults;
                final items = _filterDreams(source);
                if (items.isEmpty && _searchQuery.isEmpty) {
                  return Center(
                    child: Text(
                      AppLocalizations.of(context)!.emptyDreamsHint,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Theme.of(context).colorScheme.onSurface.withOpacity(0.4),
                            fontSize: 36,
                          ),
                      textAlign: TextAlign.center,
                    ),
                  );
                }
                return ListView.builder(
                    reverse: true, // новые сообщения снизу
                    controller: _scrollController,
                    itemCount: items.length,
                    itemBuilder: (context, index) {
                      final dream = items[items.length - 1 - index];
                      return DreamCard(
                        dream: dream,
                        accentColor: _accentColor,
                        onLongPressStart: (details) =>
                            _openMessageMenu(dream, details.globalPosition),
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => ChangeNotifierProvider(
                                create: (_) => AnalysisProvider(context.read<AuthProvider>()),
                                child: AnalysisChatScreen(
                                  dream: dream,
                                  accentColor: _accentColor,
                                  setAccentColor: _handleAccentColorChange,
                                ),
                              ),
                            ),
                          );
                        },
                      );
                    },
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
                          ? AppLocalizations.of(context)!.editDreamHint
                          : AppLocalizations.of(context)!.writeDreamHint,
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
