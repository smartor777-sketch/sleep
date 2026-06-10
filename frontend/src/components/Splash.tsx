import { Loader2 } from 'lucide-react';

export default function Splash() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-6 px-6" data-testid="splash">
      <img src="/icon-background.png" alt="InnerCore" className="w-24 h-24 object-contain animate-pulse-soft" />
      <div className="font-display text-2xl tracking-tight">InnerCore</div>
      <div className="flex items-center gap-2 muted-text">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Просыпаемся…</span>
      </div>
    </div>
  );
}
