import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../providers/profile_provider.dart';
import '../utils/snackbar.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key, required this.onCompleted});

  final VoidCallback onCompleted;

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  static const _stepCount = 5;

  final _occupationController = TextEditingController();
  final _familyController = TextEditingController();
  final _interestsController = TextEditingController();
  final _lifeContextController = TextEditingController();
  final _ageController = TextEditingController();

  int _step = 0;
  bool _loading = false;
  String? _gender;
  String? _age;

  @override
  void dispose() {
    _occupationController.dispose();
    _familyController.dispose();
    _interestsController.dispose();
    _lifeContextController.dispose();
    _ageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final size = MediaQuery.of(context).size;
    final progress = (_step + 1) / _stepCount;

    return Positioned.fill(
      child: Material(
        color: Colors.black.withOpacity(0.10),
        child: Stack(
          children: [
            BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
              child: const SizedBox.expand(),
            ),
            Center(
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  maxWidth: 520,
                  maxHeight: size.height * 0.82,
                  minWidth: 320,
                ),
                child: Container(
                  margin: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 24,
                  ),
                  padding: const EdgeInsets.fromLTRB(22, 20, 22, 18),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surface,
                    borderRadius: BorderRadius.circular(28),
                    boxShadow: const [
                      BoxShadow(
                        blurRadius: 40,
                        color: Color(0x33000000),
                        offset: Offset(0, 18),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        AppLocalizations.of(context)!.onboardingTitle,
                        style: theme.textTheme.headlineSmall,
                      ),
                      const SizedBox(height: 16),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(999),
                        child: LinearProgressIndicator(
                          minHeight: 8,
                          value: progress,
                          backgroundColor:
                              theme.colorScheme.surfaceContainerHighest,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        AppLocalizations.of(context)!.onboardingStep(_step + 1, _stepCount),
                        style: theme.textTheme.labelMedium,
                      ),
                      const SizedBox(height: 18),
                      Expanded(
                        child: AnimatedSwitcher(
                          duration: const Duration(milliseconds: 220),
                          child: SingleChildScrollView(
                            key: ValueKey(_step),
                            child: _buildStepContent(context),
                          ),
                        ),
                      ),
                      const SizedBox(height: 18),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton(
                              style: OutlinedButton.styleFrom(
                                textStyle: theme.textTheme.labelMedium,
                              ),
                              onPressed: _loading ? null : _skipStep,
                              child: Text(AppLocalizations.of(context)!.skip),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: ElevatedButton(
                              style: ElevatedButton.styleFrom(
                                textStyle: theme.textTheme.labelMedium,
                              ),
                              onPressed: _loading ? null : _continueOrFinish,
                              child: _loading
                                  ? const SizedBox(
                                      height: 16,
                                      width: 16,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : Text(
                                      _step == _stepCount - 1
                                          ? AppLocalizations.of(context)!.finish
                                          : AppLocalizations.of(context)!.next,
                                    ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStepContent(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    switch (_step) {
      case 0:
        return _buildGenderAndAge(context);
      case 1:
        return _buildTextStep(
          context,
          title: l10n.occupationQuestion,
          subtitle: l10n.occupationHint,
          controller: _occupationController,
          hintText: l10n.occupationPlaceholder,
        );
      case 2:
        return _buildTextStep(
          context,
          title: l10n.familyQuestion,
          subtitle: l10n.familyHint,
          controller: _familyController,
          hintText: l10n.familyPlaceholder,
        );
      case 3:
        return _buildTextStep(
          context,
          title: l10n.interestsQuestion,
          subtitle: l10n.interestsHint,
          controller: _interestsController,
          hintText: l10n.interestsPlaceholder,
        );
      default:
        return _buildTextStep(
          context,
          title: l10n.lifeContextQuestion,
          subtitle: l10n.lifeContextHint,
          controller: _lifeContextController,
          hintText: l10n.lifeContextPlaceholder,
          multiline: true,
        );
    }
  }

  Widget _buildGenderAndAge(BuildContext context) {
    final theme = Theme.of(context);
    const genders = <({String key, IconData icon})>[
      (key: 'female', icon: Icons.female_rounded),
      (key: 'male', icon: Icons.male_rounded),
      (key: 'unknown', icon: Icons.question_mark_rounded),
    ];
    final borderColor = theme.colorScheme.outline.withOpacity(0.35);

    Widget genderButton(({String key, IconData icon}) option) {
      final selected = _gender == option.key;
      return InkWell(
        borderRadius: BorderRadius.circular(999),
        onTap: _loading
            ? null
            : () {
                setState(() {
                  _gender = selected ? null : option.key;
                });
              },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          width: 64,
          height: 64,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: selected
                ? theme.colorScheme.primary.withOpacity(0.12)
                : theme.colorScheme.surface,
            border: Border.all(
              color: selected ? theme.colorScheme.primary : borderColor,
              width: selected ? 2 : 1.2,
            ),
          ),
          child: Icon(
            option.icon,
            color: selected
                ? theme.colorScheme.primary
                : theme.colorScheme.onSurface.withOpacity(0.78),
            size: 28,
          ),
        ),
      );
    }

    ;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          AppLocalizations.of(context)!.onboardingIntro,
          style: theme.textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        Text(
          AppLocalizations.of(context)!.onboardingGenderNote,
          style: theme.textTheme.bodyMedium,
        ),
        const SizedBox(height: 18),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: genders.map(genderButton).toList(),
        ),
        const SizedBox(height: 18),
        Text(
          AppLocalizations.of(context)!.ageLabel,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurface.withOpacity(0.7),
          ),
        ),
        const SizedBox(height: 10),
        _AgePicker(
          controller: _ageController,
          enabled: !_loading,
          onChanged: (value) => setState(() => _age = value),
        ),
      ],
    );
  }

  Widget _buildTextStep(
    BuildContext context, {
    required String title,
    required String subtitle,
    required TextEditingController controller,
    required String hintText,
    bool multiline = false,
  }) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: theme.textTheme.titleMedium),
        const SizedBox(height: 8),
        Text(subtitle, style: theme.textTheme.bodyMedium),
        const SizedBox(height: 18),
        TextField(
          controller: controller,
          maxLines: multiline ? 8 : 4,
          minLines: multiline ? 6 : 3,
          decoration: InputDecoration(
            hintText: hintText,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            alignLabelWithHint: multiline,
          ),
        ),
      ],
    );
  }

  void _skipStep() {
    if (_step == _stepCount - 1) {
      _submit();
      return;
    }
    setState(() {
      if (_step == 0) {
        _gender = null;
        _age = null;
        _ageController.clear();
      } else if (_step == 1) {
        _occupationController.clear();
      } else if (_step == 2) {
        _familyController.clear();
      } else if (_step == 3) {
        _interestsController.clear();
      }
      _step += 1;
    });
  }

  void _continueOrFinish() {
    if (_step == _stepCount - 1) {
      _submit();
      return;
    }
    setState(() {
      _step += 1;
    });
  }

  Future<void> _submit() async {
    setState(() => _loading = true);
    final updated = await context.read<ProfileProvider>().saveAboutMe(
      _buildAboutMePayload(),
      onboardingCompleted: true,
    );
    if (!mounted) return;
    setState(() => _loading = false);
    if (updated == null) {
      showToast(context, AppLocalizations.of(context)!.onboardingFailed, isError: true);
      return;
    }
    widget.onCompleted();
  }

  String _buildAboutMePayload() {
    final parts = <String>[];
    final occupation = _occupationController.text.trim();
    final family = _familyController.text.trim();
    final interests = _interestsController.text.trim();
    final lifeContext = _lifeContextController.text.trim();

    if ((_gender ?? '').isNotEmpty) {
      parts.add(_mapGenderLabel(_gender!));
    }
    if ((_age ?? '').isNotEmpty) {
      parts.add(AppLocalizations.of(context)!.ageYears(_age!));
    }
    if (occupation.isNotEmpty) {
      parts.add(occupation);
    }
    if (family.isNotEmpty) {
      parts.add(family);
    }
    if (interests.isNotEmpty) {
      parts.add(interests);
    }
    if (lifeContext.isNotEmpty) {
      parts.add(lifeContext);
    }

    return parts.join('; ');
  }

  String _mapGenderLabel(String value) {
    final l10n = AppLocalizations.of(context)!;
    switch (value) {
      case 'female':
        return l10n.genderFemale;
      case 'male':
        return l10n.genderMale;
      default:
        return l10n.genderUnspecified;
    }
  }
}

class _AgePicker extends StatelessWidget {
  final TextEditingController controller;
  final bool enabled;
  final ValueChanged<String?> onChanged;

  const _AgePicker({
    required this.controller,
    required this.enabled,
    required this.onChanged,
  });

  static const int _min = 12;
  static const int _max = 90;
  static const int _default = 25;

  int? _parsed() {
    final raw = controller.text.trim();
    if (raw.isEmpty) return null;
    return int.tryParse(raw);
  }

  void _bump(int delta) {
    final current = _parsed() ?? _default;
    final next = (current + delta).clamp(_min, _max);
    controller.text = next.toString();
    controller.selection = TextSelection.collapsed(offset: controller.text.length);
    onChanged(controller.text);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final accent = theme.colorScheme.primary;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withOpacity(0.4),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Row(
        children: [
          _RoundIconButton(
            icon: Icons.remove,
            onPressed: enabled ? () => _bump(-1) : null,
            accent: accent,
          ),
          Expanded(
            child: TextField(
              controller: controller,
              enabled: enabled,
              keyboardType: const TextInputType.numberWithOptions(decimal: false, signed: false),
              inputFormatters: [
                FilteringTextInputFormatter.digitsOnly,
                LengthLimitingTextInputFormatter(2),
              ],
              textAlign: TextAlign.center,
              style: theme.textTheme.displaySmall?.copyWith(
                fontWeight: FontWeight.w600,
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
              decoration: const InputDecoration(
                hintText: '—',
                border: InputBorder.none,
                isDense: true,
                contentPadding: EdgeInsets.symmetric(vertical: 4),
              ),
              onChanged: (raw) {
                if (raw.isEmpty) {
                  onChanged(null);
                  return;
                }
                final n = int.tryParse(raw);
                if (n == null) {
                  onChanged(null);
                  return;
                }
                final clamped = n.clamp(_min, _max);
                if (clamped != n) {
                  final s = clamped.toString();
                  controller.text = s;
                  controller.selection = TextSelection.collapsed(offset: s.length);
                  onChanged(s);
                } else {
                  onChanged(raw);
                }
              },
            ),
          ),
          _RoundIconButton(
            icon: Icons.add,
            onPressed: enabled ? () => _bump(1) : null,
            accent: accent,
          ),
        ],
      ),
    );
  }
}

class _RoundIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onPressed;
  final Color accent;
  const _RoundIconButton({required this.icon, required this.onPressed, required this.accent});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: accent.withOpacity(0.12),
      shape: const CircleBorder(),
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onPressed,
        child: SizedBox(
          width: 44,
          height: 44,
          child: Icon(icon, color: accent),
        ),
      ),
    );
  }
}
