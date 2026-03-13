import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

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
  static final _ages = [for (var age = 12; age <= 90; age++) '$age'];

  final _occupationController = TextEditingController();
  final _familyController = TextEditingController();
  final _interestsController = TextEditingController();
  final _lifeContextController = TextEditingController();

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
                        'Давайте познакомимся',
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
                        'Шаг ${_step + 1} из $_stepCount',
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
                              child: const Text('Пропустить'),
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
                                          ? 'Завершить'
                                          : 'Далее',
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
    switch (_step) {
      case 0:
        return _buildGenderAndAge(context);
      case 1:
        return _buildTextStep(
          context,
          title: 'Чем вы сейчас занимаетесь?',
          subtitle:
              'Например: студент, работа в найме, предпринимательство, творческая деятельность.',
          controller: _occupationController,
          hintText: 'Расскажите о своём занятии',
        );
      case 2:
        return _buildTextStep(
          context,
          title: 'Расскажите немного о семье или близких людях',
          subtitle:
              'Например: живёте ли вы один, есть ли партнёр, дети или важные отношения.',
          controller: _familyController,
          hintText: 'Ваш социальный контекст',
        );
      case 3:
        return _buildTextStep(
          context,
          title: 'Какие у вас увлечения или интересы?',
          subtitle:
              'Искусство, спорт, технологии, путешествия или что-то совсем своё.',
          controller: _interestsController,
          hintText: 'Ваши интересы',
        );
      default:
        return _buildTextStep(
          context,
          title: 'Что сейчас особенно важно в вашей жизни?',
          subtitle:
              'Можно рассказать о целях, трудностях, изменениях или поисках.',
          controller: _lifeContextController,
          hintText: 'Текущий жизненный контекст',
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
          'Чтобы лучше понимать контекст ваших снов, расскажите немного о себе.',
          style: theme.textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        Text(
          'Пол и возраст можно пропустить, если не хочется отвечать.',
          style: theme.textTheme.bodyMedium,
        ),
        const SizedBox(height: 18),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: genders.map(genderButton).toList(),
        ),
        const SizedBox(height: 18),
        DropdownButtonFormField<String>(
          initialValue: _age,
          items: _ages
              .map(
                (age) => DropdownMenuItem<String>(value: age, child: Text(age)),
              )
              .toList(),
          onChanged: _loading
              ? null
              : (value) {
                  setState(() {
                    _age = value;
                  });
                },
          decoration: InputDecoration(
            labelText: 'Возраст',
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
            ),
          ),
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
      showToast(context, 'Не удалось завершить онбординг', isError: true);
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
      parts.add('$_age лет');
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
    switch (value) {
      case 'female':
        return 'Женщина';
      case 'male':
        return 'Мужчина';
      default:
        return 'Предпочитает не указывать пол';
    }
  }
}
