class UserMe {
  final String id;
  final String? email;
  final bool isAnonymous;
  final List<String> linkedProviders;
  final String? aboutMe;

  UserMe({
    required this.id,
    required this.email,
    required this.isAnonymous,
    required this.linkedProviders,
    required this.aboutMe,
  });

  factory UserMe.fromJson(Map<String, dynamic> json) {
    final profile = json['profile'] as Map<String, dynamic>?;
    return UserMe(
      id: json['id'] as String,
      email: json['email'] as String?,
      isAnonymous: json['is_anonymous'] as bool? ?? true,
      linkedProviders: (json['linked_providers'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
      aboutMe: profile?['about_me'] as String?,
    );
  }
}
