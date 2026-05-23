import { ReactNode, useEffect } from 'react';
import { X } from 'lucide-react';
import clsx from 'clsx';

interface Props {
  open: boolean;
  onClose?: () => void;
  children: ReactNode;
  title?: string;
  size?: 'sm' | 'md' | 'lg';
  closable?: boolean;
  testId?: string;
}

export default function Modal({ open, onClose, children, title, size = 'md', closable = true, testId }: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && closable && onClose) onClose();
    };
    window.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [open, onClose, closable]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4" data-testid={testId}>
      <div
        className="absolute inset-0 bg-black/55 backdrop-blur-sm animate-fade-up"
        onClick={() => closable && onClose?.()}
      />
      <div
        className={clsx(
          'relative glass rounded-t-[28px] sm:rounded-[28px] w-full overflow-hidden animate-fade-up',
          size === 'sm' && 'sm:max-w-md',
          size === 'md' && 'sm:max-w-xl',
          size === 'lg' && 'sm:max-w-3xl'
        )}
        style={{ maxHeight: '92vh' }}
      >
        {(title || closable) && (
          <div className="flex items-center justify-between px-5 pt-5">
            <h2 className="font-display text-xl">{title}</h2>
            {closable && (
              <button
                onClick={() => onClose?.()}
                className="w-9 h-9 rounded-full btn-ghost flex items-center justify-center"
                data-testid="modal-close-btn"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        )}
        <div className="px-5 pb-5 pt-3 overflow-y-auto" style={{ maxHeight: 'calc(92vh - 60px)' }}>
          {children}
        </div>
      </div>
    </div>
  );
}
