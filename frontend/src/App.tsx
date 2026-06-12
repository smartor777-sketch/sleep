import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useApp } from './lib/store';
import { setApiHandlers } from './lib/api';
import Layout from './components/Layout';
import TodayPage from './pages/TodayPage';
import DreamsPage from './pages/DreamsPage';
import DreamPage from './pages/DreamPage';
import MapPage from './pages/MapPage';
import SearchPage from './pages/SearchPage';
import AnalyticsPage from './pages/AnalyticsPage';
import ProfilePage from './pages/ProfilePage';
import AuthPromptModal from './components/AuthPromptModal';
import OnboardingModal from './components/OnboardingModal';
import PaywallModal from './components/PaywallModal';
import Splash from './components/Splash';

export default function App() {
  const bootstrap = useApp((s) => s.bootstrap);
  const ready = useApp((s) => s.ready);
  const bootstrapping = useApp((s) => s.bootstrapping);
  const setUpgradeBanner = useApp((s) => s.setUpgradeBanner);

  useEffect(() => {
    setApiHandlers({
      onUpgradeRequired: (info) => setUpgradeBanner(info),
      onForceLogout: () => {
        // anonymous bootstrap again
        useApp.getState().bootstrap();
      },
    });
    bootstrap();
  }, [bootstrap, setUpgradeBanner]);

  if (bootstrapping || !ready) return <Splash />;

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<TodayPage />} />
        <Route path="/dreams" element={<DreamsPage />} />
        <Route path="/dream/:id" element={<DreamPage />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <AuthPromptModal />
      <OnboardingModal />
      <PaywallModal />
    </Layout>
  );
}
