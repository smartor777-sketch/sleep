import { Loader2 } from 'lucide-react';

export default function Splash() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-6 px-6" data-testid="splash">
      <div className="relative w-24 h-24 rounded-3xl overflow-hidden animate-pulse-soft">
        <img src="/icon-background.png" alt="" aria-hidden="true" className="absolute inset-0 w-full h-full object-cover" />
        <img src="/icon.png" alt="InnerCore" className="absolute inset-0 w-full h-full object-contain" />
      </div>
      <div className="font-display text-2xl tracking-tight">InnerCore</div>
      <div className="flex items-center gap-2 muted-text">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Просыпаемся…</span>
      </div>
    </div>
  );
}
