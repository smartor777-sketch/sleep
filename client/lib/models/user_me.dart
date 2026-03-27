class UserMe {
  final String id;
  final String? email;
  final bool isAnonymous;
  final bool emailVerified;
  final List<String> linkedProviders;
  final String? aboutMe;
  final bool onboardingCompleted;

  UserMe({
    required this.id,
    required this.email,
    required this.isAnonymous,
    this.emailVerified = false,
    required this.linkedProviders,
    required this.aboutMe,
    required this.onboardingCompleted,
  });

  factory UserMe.fromJson(Map<String, dynamic> json) {
    final profile = json['profile'] as Map<String, dynamic>?;
    return UserMe(
      id: json['id'] as String,
      email: json['email'] as String?,
      isAnonymous: json['is_anonymous'] as bool? ?? true,
      emailVerified: json['email_verified'] as bool? ?? false,
      linkedProviders: (json['linked_providers'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
      aboutMe: profile?['about_me'] as String?,
      onboardingCompleted: profile?['onboarding_completed'] as bool? ?? false,
    );
  }

  UserMe copyWith({
    String? id,
    String? email,
    bool? isAnonymous,
    bool? emailVerified,
    List<String>? linkedProviders,
    String? aboutMe,
    bool? onboardingCompleted,
  }) {
    return UserMe(
      id: id ?? this.id,
      email: email ?? this.email,
      isAnonymous: isAnonymous ?? this.isAnonymous,
      emailVerified: emailVerified ?? this.emailVerified,
      linkedProviders: linkedProviders ?? this.linkedProviders,
      aboutMe: aboutMe ?? this.aboutMe,
      onboardingCompleted: onboardingCompleted ?? this.onboardingCompleted,
    );
  }
}
