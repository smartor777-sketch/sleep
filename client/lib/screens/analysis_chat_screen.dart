import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../l10n/app_localizations.dart';
import '../widgets/message_bubble.dart';
import '../models/dream.dart';
import '../providers/analysis_provider.dart';
import '../models/analysis_message.dart';
import '../providers/dreams_provider.dart';

class AnalysisChatScreen extends StatefulWidget {
  final Dream dream;
  final Color accentColor;
  final Function(Color) setAccentColor;

  const AnalysisChatScreen({
    super.key,
    required this.dream,
    required this.accentColor,
    required this.setAccentColor,
  });

  @override
  State<AnalysisChatScreen> createState() => _AnalysisChatScreenState();
}

class _AnalysisChatScreenState extends State<AnalysisChatScreen> {
  final TextEditingController _controller = TextEditingController();
  late Color _accentColor;
  late String _dreamTitle;

  @override
  void initState() {
    super.initState();
    _accentColor = widget.accentColor;
    _dreamTitle = widget.dream.title ?? '';
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AnalysisProvider>().load(widget.dream);
    });
  }

  @override
  void didUpdateWidget(covariant AnalysisChatScreen oldWidget) {
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

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  String _mapAnalysisError(String? message) {
    final l10n = AppLocalizations.of(context)!;
    if (message == 'analysis_failed') return l10n.analysisFailed;
    if (message == 'message_failed') return l10n.messageFailed;
    if (message == 'network_error') return l10n.networkError;
    return l10n.genericError;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.dreamAnalysisTitle),
            Text(
              _formatDateTime(widget.dream.createdAt),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                    fontSize: 12,
                  ),
            ),
          ],
        ),
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'edit_title') {
                _openEditTitleDialog(context);
              } else if (value == 'delete_dream') {
                _confirmDeleteDream(context);
              }
            },
            itemBuilder: (context) {
              return [
                PopupMenuItem(
                  value: 'edit_title',
                  child: Text(l10n.editTitleLabel),
                ),
                PopupMenuItem(
                  value: 'delete_dream',
                  child: Text(l10n.delete),
                ),
              ];
            },
            icon: const Icon(Icons.more_vert),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: Consumer<AnalysisProvider>(
              builder: (context, provider, _) {
                if (provider.error != null) {
                  WidgetsBinding.instance.addPostFrameCallback((_) {
                    _showError(_mapAnalysisError(provider.error));
                    provider.clearError();
                  });
                }
                final messages = provider.messages;
                if (provider.loading && messages.isEmpty && !provider.showDreamIntro) {
                  return const Center(child: CircularProgressIndicator());
                }
                final showDreamIntro = provider.showDreamIntro;
                final totalCount = messages.length + (showDreamIntro ? 1 : 0);
                return ListView.builder(
                  reverse: true,
                  itemCount: totalCount,
                  itemBuilder: (context, index) {
                    if (showDreamIntro && index == totalCount - 1) {
                      return MessageBubble(
                        message: widget.dream.content,
                        isUserMessage: true,
                        accentColor: _accentColor,
                      );
                    }
                    final message = messages[messages.length - 1 - index];
                    return MessageBubble(
                      message: message.content,
                      isUserMessage: message.role == MessageRole.user,
                      accentColor: _accentColor,
                    );
                  },
                );
              },
            ),
          ),
          Consumer<AnalysisProvider>(
            builder: (context, provider, _) {
              if (!provider.loading && !provider.analysisInProgress) return const SizedBox.shrink();
              return const Padding(
                padding: EdgeInsets.all(8.0),
                child: CircularProgressIndicator(),
              );
            },
          ),
          Consumer<AnalysisProvider>(
            builder: (context, provider, _) {
              if (!provider.analysisReady) {
                return Padding(
                  padding: const EdgeInsets.all(12),
                  child: SizedBox(
                    width: double.infinity,
                  child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _accentColor,
                        foregroundColor: Colors.white,
                      ),
                      onPressed: provider.analysisInProgress
                          ? null
                          : () async {
                              await context.read<AnalysisProvider>().startAnalysis();
                            },
                      child: provider.analysisInProgress
                          ? Text(l10n.analyzingLabel)
                          : Text(l10n.analyze),
                    ),
                  ),
                );
              }
              return Container(
                margin: const EdgeInsets.all(12),
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
                        maxLines: null,
                        decoration: InputDecoration(
                          hintText: l10n.writeMessageHint,
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
                        onPressed: () async {
                          final text = _controller.text.trim();
                          if (text.isEmpty) return;
                          _controller.clear();
                          await context.read<AnalysisProvider>().sendMessage(widget.dream.id, text);
                          if (context.read<AnalysisProvider>().error != null) {
                            _showError(l10n.messageSendError);
                          }
                        },
                      ),
                    )
                  ],
                ),
              );
            },
          )
        ],
      ),
    );
  }

  String _formatDateTime(DateTime date) {
    final day = date.day.toString().padLeft(2, '0');
    final month = date.month.toString().padLeft(2, '0');
    final year = (date.year % 100).toString().padLeft(2, '0');
    final hour = date.hour.toString().padLeft(2, '0');
    final minute = date.minute.toString().padLeft(2, '0');
    return '$day.$month.$year  $hour:$minute';
  }

  Future<void> _openEditTitleDialog(BuildContext context) async {
    final l10n = AppLocalizations.of(context)!;
    final controller = TextEditingController(text: _dreamTitle);
    final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: Text(l10n.editTitleLabel),
          content: TextField(
            controller: controller,
            decoration: InputDecoration(
              hintText: l10n.titleHint,
            ),
            maxLength: 100,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: Text(l10n.cancel),
            ),
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(controller.text),
              child: Text(l10n.ok),
            ),
          ],
        );
      },
    );
    if (!mounted || result == null) return;
    final nextTitle = result.trim();
    final updated = await context.read<DreamsProvider>().updateDreamTitle(
          widget.dream.id,
          nextTitle.isEmpty ? null : nextTitle,
        );
    if (updated == null) {
      _showError(AppLocalizations.of(context)!.dreamSaveError);
      return;
    }
    setState(() {
      _dreamTitle = updated.title ?? '';
    });
  }

  Future<void> _confirmDeleteDream(BuildContext context) async {
    final l10n = AppLocalizations.of(context)!;
    final shouldDelete = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: Text(l10n.delete),
          content: Text(l10n.deleteDreamConfirm),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: Text(l10n.cancel),
            ),
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: Text(l10n.ok),
            ),
          ],
        );
      },
    );
    if (!mounted || shouldDelete != true) return;
    final ok = await context.read<DreamsProvider>().deleteDream(widget.dream.id);
    if (!ok) {
      _showError(AppLocalizations.of(context)!.dreamDeleteError);
      return;
    }
    if (mounted) Navigator.of(context).pop();
  }
}
