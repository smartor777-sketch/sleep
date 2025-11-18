class UserProfile {
  String email;
  String aboutMe;
  int totalDreams;
  int streak;
  Map<String, int> weekdayStats;

  UserProfile({
    required this.email,
    this.aboutMe = '',
    this.totalDreams = 0,
    this.streak = 0,
    Map<String, int>? weekdayStats,
  }) : weekdayStats = weekdayStats ?? {
          'Mon': 0,
          'Tue': 0,
          'Wed': 0,
          'Thu': 0,
          'Fri': 0,
          'Sat': 0,
          'Sun': 0,
        };
}