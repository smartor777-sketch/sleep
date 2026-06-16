import { ReactNode, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

const NEW_DREAM_EVENT = 'innercore:new-dream';

export function emitNewDreamRequest() {
  window.dispatchEvent(new CustomEvent(NEW_DREAM_EVENT));
}

export function onNewDreamRequest(handler: () => void) {
  const wrapped = () => handler();
  window.addEventListener(NEW_DREAM_EVENT, wrapped);
  return () => window.removeEventListener(NEW_DREAM_EVENT, wrapped);
}

export default function Layout({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const loc = useLocation();
  const isToday = loc.pathname === '/';
  const isMap = loc.pathname === '/map';

  // Close drawer on Esc
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSidebarOpen(false);
      if ((e.metaKey || e.ctrlKey) && (e.key === 'n' || e.key === 'N')) {
        e.preventDefault();
        emitNewDreamRequest();
        if (location.pathname !== '/') {
          // SPA-friendly nav
          history.pushState({}, '', '/');
          window.dispatchEvent(new PopStateEvent('popstate'));
        }
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <div className="grain min-h-screen flex relative">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewDream={() => emitNewDreamRequest()}
      />

      <div className="flex-1 min-w-0 flex flex-col">
        <Topbar onOpenSidebar={() => setSidebarOpen(true)} />
        <main
          className={`flex-1 pt-4 sm:pt-6 pb-12 w-full relative z-10 ${
            isMap
              ? 'px-0 max-w-none'
              : `px-3 sm:px-6 lg:px-8 mx-auto ${isToday ? 'max-w-none' : 'max-w-[1280px]'}`
          }`}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
