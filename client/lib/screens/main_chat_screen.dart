import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import '../l10n/app_localizations.dart';
import '../widgets/dream_card.dart';
import '../widgets/message_menu.dart';
import '../models/dream.dart';
import '../providers/auth_provider.dart';
import '../providers/dreams_provider.dart';
import '../providers/analysis_provider.dart';
import 'profile_screen.dart';
import 'analysis_chat_screen.dart';
import '../utils/snackbar.dart';

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
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _speechReady = false;
  bool _isListening = false;
  List<stt.LocaleName>? _speechLocales;
  String? _speechLocaleId;
  String? _speechLocaleCode;

  Dream? _editingDream;
  bool _showSearch = false;
  String _searchQuery = '';
  DateTime? _selectedDate;
  bool _showHeader = true;
  double _prevScrollOffset = 0;

  // Добавляем сон или редактируем существующий
  Future<void> _sendMessage() async {
    if (_isListening) {
      await _speech.stop();
      if (mounted) setState(() => _isListening = false);
    }
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
    _scrollController.addListener(_handleScroll);
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

  Future<void> _toggleListening() async {
    if (_isListening) {
      await _speech.stop();
      if (!mounted) return;
      setState(() => _isListening = false);
      return;
    }

    if (!_speechReady) {
      _speechReady = await _speech.initialize();
    }
    if (!_speechReady) {
      _showError(AppLocalizations.of(context)!.genericError);
      return;
    }
    _speechLocales ??= await _speech.locales();
    final desiredCode = Localizations.localeOf(context).languageCode.toLowerCase();
    if (_speechLocaleCode != desiredCode) {
      _speechLocaleCode = desiredCode;
      _speechLocaleId = _selectLocaleId(desiredCode);
    }

    setState(() => _isListening = true);
    await _speech.listen(
      onResult: (result) {
        if (!mounted) return;
        setState(() {
          _controller.text = result.recognizedWords;
          _controller.selection = TextSelection.fromPosition(
            TextPosition(offset: _controller.text.length),
          );
        });
      },
      listenMode: stt.ListenMode.dictation,
      partialResults: true,
      localeId: _speechLocaleId,
    );
  }

  String? _selectLocaleId(String languageCode) {
    final locales = _speechLocales;
    if (locales == null || locales.isEmpty) return null;
    for (final locale in locales) {
      final id = locale.localeId.toLowerCase();
      if (id == languageCode || id.startsWith('$languageCode-') || id.startsWith('${languageCode}_')) {
        return locale.localeId;
      }
    }
    return null;
  }

  void _handleScroll() {
    if (!_scrollController.hasClients) return;
    final current = _scrollController.offset;
    final diff = current - _prevScrollOffset;
    // reverse: true list — offset increases when scrolling towards older (visual UP)
    if (diff > 3 && !_showHeader) {
      setState(() => _showHeader = true);
    } else if (diff < -3 && _showHeader) {
      setState(() => _showHeader = false);
    }
    _prevScrollOffset = current;
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
        showToast(context, AppLocalizations.of(context)!.dreamCopied);
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
    showToast(context, message, isError: true);
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
  void dispose() {
    _speech.stop();
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Animated header — hides on scroll down, shows on scroll up
            ClipRect(
              child: AnimatedAlign(
                duration: const Duration(milliseconds: 250),
                curve: Curves.easeInOut,
                alignment: Alignment.topCenter,
                heightFactor: _showHeader ? 1.0 : 0.0,
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  child: Row(
                    children: [
                      const SizedBox(width: 8),
                      Text('JungAI', style: Theme.of(context).textTheme.titleLarge),
                      const Spacer(),
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
                ),
              ),
            ),
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
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 24),
                      child: Text(
                        AppLocalizations.of(context)!.emptyDreamsHint,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.4),
                              fontSize: 36,
                            ),
                        textAlign: TextAlign.center,
                      ),
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
          Padding(
            padding: const EdgeInsets.fromLTRB(4, 2, 4, 4),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                AnimatedSize(
                  duration: const Duration(milliseconds: 200),
                  child: _isListening
                      ? Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.circle, color: Colors.red, size: 8),
                              const SizedBox(width: 6),
                              Text(
                                l10n.listeningLabel,
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                      color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
                                    ),
                              ),
                            ],
                          ),
                        )
                      : const SizedBox.shrink(),
                ),
                Row(
                  children: [
                    IconButton(
                      icon: Icon(_isListening ? Icons.mic_off : Icons.mic, color: _accentColor),
                      onPressed: _toggleListening,
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                    ),
                    Expanded(
                      child: TextField(
                        controller: _controller,
                        minLines: 1,
                        maxLines: 5,
                        style: const TextStyle(fontSize: 14),
                        decoration: InputDecoration(
                          hintText: _editingDream != null
                              ? l10n.editDreamHint
                              : l10n.writeDreamHint,
                          border: InputBorder.none,
                          isDense: true,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                        ),
                      ),
                    ),
                    Container(
                      decoration: BoxDecoration(
                        color: _accentColor,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: IconButton(
                        icon: const Icon(Icons.send, color: Colors.white, size: 20),
                        onPressed: _sendMessage,
                        padding: EdgeInsets.zero,
                        constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          ],
        ),
      ),
    );
  }
}
