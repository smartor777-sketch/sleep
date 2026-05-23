import { Loader2 } from 'lucide-react';

export default function Splash() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-6 px-6" data-testid="splash">
      <div className="relative w-24 h-24">
        <div
          className="absolute inset-0 rounded-full"
          style={{ background: 'radial-gradient(circle at 30% 30%, #FA9042, #8885FF 70%)', filter: 'blur(2px)' }}
        />
        <div className="absolute inset-0 rounded-full animate-pulse-soft" style={{
          boxShadow: '0 0 60px 10px rgba(136,133,255,0.45), inset 0 0 30px rgba(0,0,0,0.4)'
        }} />
      </div>
      <div className="font-display text-2xl tracking-tight">InnerCore</div>
      <div className="flex items-center gap-2 muted-text">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Просыпаемся…</span>
      </div>
    </div>
  );
}
