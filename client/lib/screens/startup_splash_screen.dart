import 'package:flutter/material.dart';

class StartupSplashScreen extends StatefulWidget {
  const StartupSplashScreen({super.key});

  @override
  State<StartupSplashScreen> createState() => _StartupSplashScreenState();
}

class _StartupSplashScreenState extends State<StartupSplashScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final CurvedAnimation _progressAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3600),
    )..forward();
    _progressAnimation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            const logoSize = 142.0;
            final progress = 0.08 + (_progressAnimation.value * 0.84);
            return Stack(
              alignment: Alignment.center,
              children: [
                SizedBox(
                  width: 164,
                  height: 164,
                  child: CircularProgressIndicator(
                    value: progress,
                    strokeWidth: 5,
                    strokeCap: StrokeCap.round,
                    backgroundColor: const Color(0x1A6F42C1),
                    valueColor: const AlwaysStoppedAnimation<Color>(
                      Color(0xFF6F42C1),
                    ),
                  ),
                ),
                SizedBox(
                  width: logoSize,
                  height: logoSize,
                  child: ClipOval(
                    child: Image.asset(
                      'icon_transparent.png',
                      fit: BoxFit.cover,
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
