import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../models/dream.dart';
import '../providers/dream_map_provider.dart';
import '../providers/analysis_provider.dart';
import '../providers/auth_provider.dart';
import '../providers/dreams_provider.dart';
import '../services/api_exception.dart';
import '../services/voice_input_service.dart';
import '../utils/snackbar.dart';
import '../widgets/dream_card.dart';
import '../widgets/message_menu.dart';
import 'analysis_chat_screen.dart';
import 'dream_map_screen.dart';
import 'profile_screen.dart';

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
  static const _tabGrid = 0;
  static const _tabChat = 1;
  static const _tabMap = 3;
  static const _tabProfile = 4;

  final TextEditingController _controller = TextEditingController();
  final FocusNode _searchFocusNode = FocusNode();
  late final VoiceInputService _voiceService;

  Dream? _editingDream;
  Dream? _selectedDream;
  AnalysisProvider? _analysisProvider;
  bool _showSearch = false;
  String _searchQuery = '';
  bool _submittingDream = false;
  int _currentTab = _tabGrid;
  late Color _accentColor;

  Future<void> _sendMessage() async {
    if (_submittingDream) {
      return;
    }
    if (_voiceService.isRecording) {
      await _stopRecordingAndTranscribe();
      return;
    }
    if (_voiceService.isTranscribing) {
      return;
    }

    final text = _controller.text.trim();
    if (text.isEmpty) return;

    final provider = context.read<DreamsProvider>();
    final l10n = AppLocalizations.of(context)!;
    setState(() => _submittingDream = true);
    try {
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
        _showError(_mapDreamsError(provider.errorCode, provider.error));
        return;
      }
      _controller.clear();
    } finally {
      if (mounted) {
        setState(() => _submittingDream = false);
      }
    }
  }

  @override
  void initState() {
    super.initState();
    _accentColor = widget.accentColor;
    _voiceService = VoiceInputService(
      apiClient: context.read<AuthProvider>().apiClient,
    );
    _voiceService.onStateChanged = () {
      if (mounted) setState(() {});
    };
    _voiceService.onRecordingWarning = () {
      if (mounted) {
        final l10n = AppLocalizations.of(context)!;
        showToast(context, l10n.recordingWarning);
      }
    };
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
  }

  void _handleAccentColorChange(Color color) {
    if (_accentColor == color) return;
    setState(() {
      _accentColor = color;
    });
    widget.setAccentColor(color);
  }

  void _openDreamChat(Dream dream) {
    _analysisProvider?.dispose();
    _analysisProvider = AnalysisProvider(context.read<AuthProvider>());
    setState(() {
      _selectedDream = dream;
      _currentTab = _tabChat;
      _showSearch = false;
    });
  }

  Future<void> _openDreamChatById(String dreamId) async {
    final dreams = context.read<DreamsProvider>().dreams;
    Dream? target;
    for (final dream in dreams) {
      if (dream.id == dreamId) {
        target = dream;
        break;
      }
    }
    target ??= await context.read<DreamsProvider>().refreshDream(dreamId);
    if (!mounted || target == null) return;
    _openDreamChat(target);
  }

  void _activateSearch() {
    setState(() {
      _currentTab = _tabGrid;
      _showSearch = true;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _searchFocusNode.requestFocus();
    });
  }

  void _showGrid() {
    setState(() {
      _currentTab = _tabGrid;
      _showSearch = false;
      _searchQuery = '';
    });
    context.read<DreamsProvider>().search('');
  }

  void _showMap() {
    setState(() {
      _currentTab = _tabMap;
      _showSearch = false;
    });
  }

  void _showProfile() {
    setState(() {
      _currentTab = _tabProfile;
      _showSearch = false;
    });
  }

  Future<void> _toggleRecording() async {
    if (_voiceService.isTranscribing) return;
    if (_voiceService.isRecording) {
      await _stopRecordingAndTranscribe();
    } else {
      final ok = await _voiceService.startRecording();
      if (!ok && mounted) {
        _showError(AppLocalizations.of(context)!.genericError);
      }
    }
  }

  Future<void> _stopRecordingAndTranscribe() async {
    final l10n = AppLocalizations.of(context)!;
    try {
      final result = await _voiceService.stopAndTranscribe(
        languageCode: Localizations.localeOf(context).languageCode.toLowerCase(),
      );
      if (!mounted || result == null) return;
      final existing = _controller.text.trim();
      final combined = existing.isEmpty ? result.text : '$existing ${result.text}';
      setState(() {
        _controller.text = combined;
        _controller.selection = TextSelection.fromPosition(
          TextPosition(offset: _controller.text.length),
        );
      });
      if (result.partial) {
        showToast(context, l10n.partialTranscription);
      }
    } on ApiException catch (e) {
      if (!mounted) return;
      _showError(e.statusCode == 503 ? l10n.networkError : l10n.genericError);
    } catch (_) {
      if (!mounted) return;
      _showError(l10n.genericError);
    }
  }

  void _openMessageMenu(Dream dream, Offset globalPosition) {
    final overlay =
        Overlay.of(context).context.findRenderObject() as RenderBox?;
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
      onEditDate: () {
        _openEditDreamDateDialog(dream);
      },
    );
  }

  Future<void> _openEditDreamDateDialog(Dream dream) async {
    final now = DateTime.now();
    final pickedDate = await showDatePicker(
      context: context,
      initialDate: dream.createdAt.isAfter(now) ? now : dream.createdAt,
      firstDate: DateTime(2020),
      lastDate: now,
    );
    if (!mounted || pickedDate == null) return;
    final pickedTime = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(dream.createdAt),
    );
    if (!mounted || pickedTime == null) return;
    final updatedDate = DateTime(
      pickedDate.year,
      pickedDate.month,
      pickedDate.day,
      pickedTime.hour,
      pickedTime.minute,
    );
    if (updatedDate.isAfter(now)) {
      _showError(AppLocalizations.of(context)!.genericError);
      return;
    }
    final updated = await context.read<DreamsProvider>().updateDreamDate(
      dream.id,
      updatedDate,
    );
    if (updated == null) {
      _showError(AppLocalizations.of(context)!.dreamSaveError);
    } else {
      showToast(context, AppLocalizations.of(context)!.savedSuccess);
    }
  }

  Future<void> _deleteDream(Dream dream) async {
    final ok = await context.read<DreamsProvider>().deleteDream(dream.id);
    if (!ok) {
      _showError(AppLocalizations.of(context)!.dreamDeleteError);
      return;
    }
    if (_selectedDream?.id == dream.id) {
      _analysisProvider?.dispose();
      _analysisProvider = null;
      setState(() {
        _selectedDream = null;
        if (_currentTab == _tabChat) {
          _currentTab = _tabGrid;
        }
      });
    }
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

  @override
  void dispose() {
    _voiceService.dispose();
    _analysisProvider?.dispose();
    _controller.dispose();
    _searchFocusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      bottomNavigationBar: _FooterNavBar(
        accentColor: _accentColor,
        selectedIndex: _showSearch ? 2 : _currentTab,
        onGridTap: _showGrid,
        onChatTap: () {
          setState(() {
            _currentTab = _tabChat;
            _showSearch = false;
          });
        },
        onSearchTap: _activateSearch,
        onMapTap: _showMap,
        onProfileTap: _showProfile,
      ),
      body: SafeArea(child: _buildCurrentTab(context, l10n)),
    );
  }

  Widget _buildCurrentTab(BuildContext context, AppLocalizations l10n) {
    switch (_currentTab) {
      case _tabChat:
        if (_selectedDream == null || _analysisProvider == null) {
          return _EmptyTabState(
            title: l10n.dreamChat,
            subtitle: l10n.dreamChatHint,
          );
        }
        return ChangeNotifierProvider<AnalysisProvider>.value(
          value: _analysisProvider!,
          child: AnalysisChatScreen(
            dream: _selectedDream!,
            accentColor: _accentColor,
            setAccentColor: _handleAccentColorChange,
            embedded: true,
            onDreamDeleted: () {
              _analysisProvider?.dispose();
              _analysisProvider = null;
              setState(() {
                _selectedDream = null;
                _currentTab = _tabGrid;
              });
            },
          ),
        );
      case _tabMap:
        return ChangeNotifierProvider(
          create: (_) => DreamMapProvider(context.read<AuthProvider>()),
          child: DreamMapScreen(
            accentColor: _accentColor,
            onOpenDream: _openDreamChatById,
          ),
        );
      case _tabProfile:
        return ProfileScreen(
          isDarkMode: widget.isDarkMode,
          toggleTheme: widget.toggleTheme,
          accentColor: _accentColor,
          setAccentColor: _handleAccentColorChange,
          setLocale: widget.setLocale,
          textScale: widget.textScale,
          setTextScale: widget.setTextScale,
          embedded: true,
        );
      case _tabGrid:
      default:
        return _buildDreamsGridTab(context, l10n);
    }
  }

  Widget _buildDreamsGridTab(BuildContext context, AppLocalizations l10n) {
    return Column(
      children: [
        if (_showSearch)
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 14, 12, 8),
            child: TextField(
              focusNode: _searchFocusNode,
              decoration: InputDecoration(
                hintText: l10n.searchHint,
                suffixIcon: IconButton(
                  icon: const Icon(Icons.close_rounded),
                  onPressed: _showGrid,
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(
                    color: Theme.of(
                      context,
                    ).colorScheme.outline.withOpacity(0.5),
                    width: 2,
                  ),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(color: _accentColor, width: 2),
                ),
              ),
              onChanged: (value) {
                setState(() => _searchQuery = value);
                _search(value);
              },
            ),
          ),
        Expanded(
          child: Consumer<DreamsProvider>(
            builder: (context, provider, _) {
              if (provider.error != null) {
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  _showError(
                    _mapDreamsError(provider.errorCode, provider.error),
                  );
                  provider.clearError();
                });
              }
              if (provider.loading && provider.dreams.isEmpty) {
                return const Center(child: CircularProgressIndicator());
              }
              final items = _searchQuery.isEmpty
                  ? provider.dreams
                  : provider.searchResults;
              if (items.isEmpty && _searchQuery.isEmpty) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Text(
                      l10n.emptyDreamsHint,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(
                          context,
                        ).colorScheme.onSurface.withOpacity(0.4),
                        fontSize: 36,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                );
              }
              return GridView.builder(
                padding: const EdgeInsets.fromLTRB(10, 8, 10, 10),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 3,
                  crossAxisSpacing: 8,
                  mainAxisSpacing: 8,
                  childAspectRatio: 1,
                ),
                itemCount: items.length,
                itemBuilder: (context, index) {
                  final dream = items[index];
                  return DreamCard(
                    dream: dream,
                    accentColor: _accentColor,
                    onLongPressStart: (details) =>
                        _openMessageMenu(dream, details.globalPosition),
                    onTap: () => _openDreamChat(dream),
                  );
                },
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(4, 2, 4, 4),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              AnimatedSize(
                duration: const Duration(milliseconds: 200),
                child: _voiceService.isRecording || _voiceService.isTranscribing
                    ? Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            _RecordingWaveform(
                              level: _voiceService.recordingLevel,
                              color: _accentColor,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              _voiceService.isTranscribing
                                  ? l10n.analyzingLabel
                                  : l10n.listeningLabel,
                              style: Theme.of(context).textTheme.bodySmall
                                  ?.copyWith(
                                    color: Theme.of(
                                      context,
                                    ).colorScheme.onSurface.withOpacity(0.7),
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
                    icon: Icon(
                      _voiceService.isRecording ? Icons.stop_rounded : Icons.mic,
                      color: _accentColor,
                    ),
                    onPressed: _submittingDream ? null : _toggleRecording,
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(
                      minWidth: 36,
                      minHeight: 36,
                    ),
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
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 8,
                        ),
                      ),
                    ),
                  ),
                  Container(
                    decoration: BoxDecoration(
                      color: _accentColor,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: IconButton(
                      icon: _submittingDream
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(
                              Icons.send,
                              color: Colors.white,
                              size: 20,
                            ),
                      onPressed: _voiceService.isTranscribing ? null : _sendMessage,
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(
                        minWidth: 36,
                        minHeight: 36,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _FooterNavBar extends StatelessWidget {
  const _FooterNavBar({
    required this.accentColor,
    required this.selectedIndex,
    required this.onGridTap,
    required this.onChatTap,
    required this.onSearchTap,
    required this.onMapTap,
    required this.onProfileTap,
  });

  final Color accentColor;
  final int selectedIndex;
  final VoidCallback onGridTap;
  final VoidCallback onChatTap;
  final VoidCallback onSearchTap;
  final VoidCallback onMapTap;
  final VoidCallback onProfileTap;

  @override
  Widget build(BuildContext context) {
    final borderColor = Theme.of(context).colorScheme.outline.withOpacity(0.16);
    final background = Theme.of(context).colorScheme.surface;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: background,
        border: Border(top: BorderSide(color: borderColor)),
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 72,
          child: Row(
            children: [
              Expanded(
                child: _FooterIconButton(
                  assetPath: 'assets/grid.svg',
                  accentColor: accentColor,
                  active: selectedIndex == 0,
                  onTap: onGridTap,
                ),
              ),
              Expanded(
                child: _FooterIconButton(
                  assetPath: 'assets/chat.svg',
                  accentColor: accentColor,
                  active: selectedIndex == 1,
                  onTap: onChatTap,
                ),
              ),
              Expanded(
                child: _FooterIconButton(
                  assetPath: 'assets/search.svg',
                  accentColor: accentColor,
                  active: selectedIndex == 2,
                  onTap: onSearchTap,
                ),
              ),
              Expanded(
                child: _FooterIconButton(
                  assetPath: 'assets/map.svg',
                  accentColor: accentColor,
                  active: selectedIndex == 3,
                  onTap: onMapTap,
                ),
              ),
              Expanded(
                child: _FooterIconButton(
                  assetPath: 'assets/person.svg',
                  accentColor: accentColor,
                  active: selectedIndex == 4,
                  onTap: onProfileTap,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FooterIconButton extends StatelessWidget {
  const _FooterIconButton({
    required this.assetPath,
    required this.accentColor,
    required this.active,
    required this.onTap,
  });

  final String assetPath;
  final Color accentColor;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final iconColor = active ? accentColor : accentColor.withOpacity(0.42);

    return InkWell(
      onTap: onTap,
      child: Center(
        child: AnimatedScale(
          duration: const Duration(milliseconds: 180),
          scale: active ? 1.0 : 0.92,
          child: SvgPicture.asset(
            assetPath,
            width: 23,
            height: 23,
            colorFilter: ColorFilter.mode(iconColor, BlendMode.srcIn),
          ),
        ),
      ),
    );
  }
}

class _EmptyTabState extends StatelessWidget {
  const _EmptyTabState({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 28),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(title, style: theme.textTheme.titleLarge),
            const SizedBox(height: 10),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.58),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RecordingWaveform extends StatelessWidget {
  const _RecordingWaveform({required this.level, required this.color});

  final double level;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final heights = <double>[0.38, 0.62, 1.0, 0.74, 0.46]
        .map<double>(
          (factor) => (8 + (18 * level * factor)).clamp(6, 24).toDouble(),
        )
        .toList();

    return SizedBox(
      width: 34,
      height: 22,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: heights
            .map(
              (height) => AnimatedContainer(
                duration: const Duration(milliseconds: 120),
                width: 4,
                height: height,
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(99),
                ),
              ),
            )
            .toList(),
      ),
    );
  }
}
