import React, { useEffect, useRef, useState } from "react";
import "@/App.css";
import { Menu, X } from "lucide-react";
import Sphere from "@/components/Sphere";
import DreamMap from "@/components/DreamMap";
import { SigilQuadrature, SigilOuroboros, KeyGlyph, FooterSeal } from "@/components/Sigils";
import FractalDots from "@/components/FractalDots";
import FractalTrees from "@/components/FractalTrees";

const APP_URL = "https://app.innercore.art";
const TG_URL = "https://t.me/post_cybercore";

const useFadeIn = () => {
  useEffect(() => {
    const els = document.querySelectorAll(".fade-in");
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            obs.unobserve(e.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
    );
    els.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, []);
};

const Nav = () => {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const close = () => setOpen(false);

  const links = [
    { href: "#what", label: "что это", testid: "nav-what" },
    { href: "#how", label: "метод", testid: "nav-how" },
    { href: "#map", label: "карта", testid: "nav-map" },
    { href: "#privacy", label: "приватность", testid: "nav-privacy" },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? "nav-scrolled" : ""}`}
      data-testid="site-nav"
    >
      <nav className="container-ms py-4 md:py-5 flex items-center justify-between">
        <a href="#top" onClick={close} className="flex items-center gap-3 no-underline" data-testid="brand-mark">
          <span style={{ color: "var(--copper)" }}>
            <SigilQuadrature size={22} />
          </span>
          <span className="font-serif text-[18px] md:text-[19px] tracking-[0.02em]" style={{ color: "var(--cream)" }}>
            innerCore
          </span>
        </a>

        <div className="hidden md:flex items-center gap-9 text-[13px]" style={{ color: "var(--stone)" }}>
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="hover:text-[color:var(--cream)] transition-colors"
              style={{ color: "inherit", textDecoration: "none" }}
              data-testid={l.testid}
            >
              {l.label}
            </a>
          ))}
        </div>

        <a href={APP_URL} className="btn-ghost nav-cta-desktop" data-testid="nav-cta">открыть →</a>

        <button
          className="md:hidden p-2 -mr-2 text-[color:var(--cream)]"
          aria-label={open ? "Закрыть меню" : "Открыть меню"}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          data-testid="mobile-menu-toggle"
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>

      {/* Mobile sheet */}
      <div
        className={`md:hidden overflow-hidden transition-all duration-300 ${open ? "max-h-[400px] opacity-100" : "max-h-0 opacity-0"}`}
        data-testid="mobile-menu"
        style={{ background: "rgba(15, 17, 24, 0.97)", borderTop: open ? "1px solid var(--hairline)" : "none" }}
      >
        <div className="container-ms py-6 flex flex-col gap-5">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={close}
              className="font-serif text-[22px]"
              style={{ color: "var(--cream)", textDecoration: "none" }}
              data-testid={`m-${l.testid}`}
            >
              {l.label}
            </a>
          ))}
          <a href={APP_URL} onClick={close} className="btn-copper mt-2 self-start" data-testid="mobile-cta">
            Открыть приложение
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M2 7 H12 M8 3 L12 7 L8 11" stroke="currentColor" strokeWidth="1.2" />
            </svg>
          </a>
        </div>
      </div>
    </header>
  );
};

const SectionFrame = ({ id, children, className = "", testid }) => (
  <section
    id={id}
    className={`relative overflow-hidden min-h-screen flex items-center ${className}`}
    data-testid={testid}
  >
    {children}
  </section>
);

const Hero = () => (
  <SectionFrame id="top" testid="hero-section">
    <div className="container-ms w-full pt-28 md:pt-24 pb-12 md:pb-16">
      <div className="grid md:grid-cols-2 gap-10 md:gap-8 items-center">
        <div className="relative order-2 md:order-1">
          <div className="flex items-center gap-3 mb-6 md:mb-7" style={{ color: "var(--stone)" }}>
            <span style={{ color: "var(--copper)" }}>
              <SigilOuroboros size={38} />
            </span>
            <span className="text-[10px] md:text-[11px] tracking-[0.32em] uppercase">opus minor · 2026</span>
          </div>
          <h1 className="font-serif text-[42px] sm:text-[58px] md:text-[68px] leading-[0.98] tracking-[-0.015em]" data-testid="hero-title">
            Карта твоих<br/>
            <span style={{ color: "var(--copper)" }}>снов.</span>
          </h1>
          <p className="mt-6 md:mt-7 max-w-[460px] text-[16px] md:text-[17px]" style={{ color: "var(--cream-dim)" }} data-testid="hero-subtitle">
            Дневник сновидений с юнгианским анализом. Записывай — и наблюдай, как из ночного потока проступает структура.
          </p>
          <div className="mt-8 md:mt-10 flex items-center gap-5 md:gap-6 flex-wrap">
            <a href={APP_URL} className="btn-copper" data-testid="hero-cta-open-app">
              Открыть приложение
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M2 7 H12 M8 3 L12 7 L8 11" stroke="currentColor" strokeWidth="1.2" />
              </svg>
            </a>
            <a href="#what" className="text-[12px] md:text-[13px] tracking-[0.12em] uppercase hover:underline" style={{ color: "var(--stone)", textDecoration: "none" }} data-testid="hero-scroll-down">
              ↓ что это
            </a>
          </div>

          <div className="mt-10 md:mt-14 flex items-center gap-3 md:gap-6 text-[11px] md:text-[12px] flex-wrap" style={{ color: "var(--stone)" }}>
            <span className="flex items-center gap-2">
              <span className="w-1 h-1 rounded-full" style={{ background: "var(--copper)" }}></span>
              архетипы
            </span>
            <span>·</span>
            <span>символы</span>
            <span>·</span>
            <span>векторная карта</span>
            <span className="hidden sm:inline">·</span>
            <span className="hidden sm:inline">e2e-шифрование</span>
          </div>
        </div>

        <div className="relative order-1 md:order-2 max-w-[420px] md:max-w-none mx-auto w-full" data-testid="hero-sphere">
          <Sphere />
          <div className="mt-2 text-center font-serif italic text-[12px] md:text-[14px] px-4" style={{ color: "var(--stone)" }}>
            quod superius sicut quod inferius — что вверху, то и внизу
          </div>
        </div>
      </div>
    </div>
  </SectionFrame>
);

const WhatItIs = () => (
  <SectionFrame id="what" testid="section-what" className="fade-in">
    <div className="absolute inset-0 pointer-events-none" data-testid="fractal-bg-what">
      <FractalDots variant="copper" density={60} opacity={0.9} />
    </div>
    <div className="container-ms relative w-full py-20 md:py-28 z-[2]">
      <div className="max-w-[760px]">
        <div className="text-[10px] md:text-[11px] tracking-[0.32em] uppercase mb-5 md:mb-6" style={{ color: "var(--copper)" }}>
          — i. prima materia
        </div>
        <p className="font-serif text-[24px] sm:text-[32px] md:text-[36px] leading-[1.3]" style={{ color: "var(--cream)" }}>
          Записывай сны простым языком. innerCore раскладывает их на <span style={{ color: "var(--copper)" }}>архетипы</span>, символы и связи с другими твоими снами. Со временем складывается карта — твоё личное бессознательное в форме.
        </p>
      </div>
    </div>
  </SectionFrame>
);

const HowItWorks = () => {
  const cards = [
    { glyph: "☿", label: "Mercurius", title: "Записать", text: "Веди дневник снов. Голосом или текстом, в любое время." },
    { glyph: "🜍", label: "Sulphur", title: "Понять", text: "Каждый сон получает разбор: архетипы, мотивы, эмоциональный тон." },
    { glyph: "🜔", label: "Sal", title: "Увидеть", text: "Сны соединяются в карту. Повторяющиеся темы становятся видимыми." },
  ];
  return (
    <SectionFrame id="how" testid="section-how" className="fade-in">
      <div className="container-ms w-full py-20 md:py-28">
        <div className="flex items-baseline justify-between mb-10 md:mb-12 flex-wrap gap-4">
          <h2 className="font-serif text-[32px] sm:text-[42px] md:text-[52px] leading-[1.02]" data-testid="how-title">
            Триада<br/>метода
          </h2>
          <div className="text-[10px] md:text-[12px] tracking-[0.32em] uppercase" style={{ color: "var(--stone)" }}>
            — ii. mercurius · sulphur · sal
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-px" style={{ background: "var(--hairline)" }}>
          {cards.map((c, i) => (
            <div key={i} className="card-ms" data-testid={`how-card-${i}`} style={{ borderRadius: 0, borderWidth: 0 }}>
              <div className="flex items-center justify-between mb-6 md:mb-7">
                <span className="glyph">{c.glyph}</span>
                <span className="text-[10px] tracking-[0.32em] uppercase" style={{ color: "var(--stone)" }}>
                  {String(i + 1).padStart(2, "0")} · {c.label}
                </span>
              </div>
              <h3 className="font-serif text-[26px] md:text-[28px] mb-3">{c.title}</h3>
              <p className="text-[15px]" style={{ color: "var(--cream-dim)" }}>{c.text}</p>
            </div>
          ))}
        </div>
      </div>
    </SectionFrame>
  );
};

const MapSection = () => (
  <SectionFrame id="map" testid="section-map" className="fade-in">
    <div className="container-ms w-full py-20 md:py-28">
      <div className="grid md:grid-cols-12 gap-8 md:gap-10 items-center">
        <div className="md:col-span-5">
          <div className="text-[10px] md:text-[11px] tracking-[0.32em] uppercase mb-5 md:mb-6" style={{ color: "var(--copper)" }}>
            — iii. mappa somniorum
          </div>
          <h2 className="font-serif text-[32px] sm:text-[44px] md:text-[52px] leading-[1.04] mb-5 md:mb-6">
            Карта снов
          </h2>
          <p className="text-[15px] md:text-[16px] mb-4" style={{ color: "var(--cream-dim)" }}>
            Каждый сон — точка. Похожие сны — кластеры. Архетипы — созвездия.
          </p>
          <p className="text-[14px] md:text-[15px] italic font-serif" style={{ color: "var(--stone)" }}>
            Математическая близость векторов — как близость смыслов.
          </p>
        </div>
        <div className="md:col-span-7" data-testid="dream-map-demo">
          <DreamMap />
        </div>
      </div>
    </div>
  </SectionFrame>
);

const Privacy = () => (
  <SectionFrame id="privacy" testid="section-privacy" className="fade-in">
    <div className="absolute inset-0 pointer-events-none" data-testid="fractal-bg-privacy">
      <FractalDots variant="cinnabar" density={64} opacity={0.85} />
    </div>
    <div className="container-ms relative w-full py-20 md:py-28 z-[2]">
      <div className="grid md:grid-cols-12 gap-8 md:gap-10 items-start max-w-[1000px] mx-auto">
        <div className="md:col-span-3 flex md:justify-end">
          <div style={{ color: "var(--copper)" }}>
            <KeyGlyph size={56} />
          </div>
        </div>
        <div className="md:col-span-9">
          <div className="text-[10px] md:text-[11px] tracking-[0.32em] uppercase mb-4 md:mb-5" style={{ color: "var(--copper)" }}>
            — iv. sigillum
          </div>
          <h2 className="font-serif text-[28px] sm:text-[38px] md:text-[44px] leading-[1.06] mb-5 md:mb-6">
            Сны не покидают тебя.
          </h2>
          <p className="text-[15px] md:text-[17px] max-w-[620px]" style={{ color: "var(--cream-dim)" }}>
            Содержимое снов шифруется на твоём устройстве перед отправкой. На сервере — только шифротекст. Ни Google, ни мы, никто другой не видит, что тебе снилось.
          </p>
        </div>
      </div>
    </div>
  </SectionFrame>
);

const DeepBlock = () => (
  <SectionFrame id="deep" testid="section-deep" className="fade-in">
    <div className="container-ms w-full py-20 md:py-28">
      <details className="border-t border-b hairline py-8 md:py-10 max-w-[900px] mx-auto" data-testid="deep-details">
        <summary className="flex items-center justify-between gap-4 cursor-pointer group">
          <h2 className="font-serif text-[22px] sm:text-[30px] md:text-[34px] leading-[1.1]">
            Для тех, кто глубже
          </h2>
          <span className="font-serif text-[26px] md:text-[28px] transition-transform" style={{ color: "var(--copper)" }} aria-hidden="true">
            +
          </span>
        </summary>
        <div className="mt-7 md:mt-8 max-w-[680px] text-[15px] md:text-[16px] space-y-4 md:space-y-5" style={{ color: "var(--cream-dim)" }}>
          <p>
            <span className="font-serif italic" style={{ color: "var(--cream)" }}>Юнгианская модель психики.</span> Сознание как малая поверхность, под которой — слои личного и коллективного бессознательного.
          </p>
          <p>
            <span className="font-serif italic" style={{ color: "var(--cream)" }}>Архетипы</span> как структурные паттерны — Тень, Анима, Самость, Герой, Мудрый старец. Они не образы, а формы, в которые отливаются образы.
          </p>
          <p>
            <span className="font-serif italic" style={{ color: "var(--cream)" }}>Векторная база данных</span> как форма для индивидуальной карты символов. Каждый сон — точка в пространстве смыслов; повторение и кластеризация раскрывают паттерн.
          </p>
          <p>
            <span className="font-serif italic" style={{ color: "var(--cream)" }}>Открытая методология.</span> Статьи о методе и его обосновании — в Telegram-канале{" "}
            <a href={TG_URL} target="_blank" rel="noreferrer" style={{ color: "var(--copper)" }} className="hover:underline" data-testid="deep-tg-link">
              CyberCore
            </a>.
          </p>
        </div>
      </details>
    </div>
  </SectionFrame>
);

const FinalCTA = () => (
  <SectionFrame id="final" testid="section-final-cta" className="fade-in">
    <div className="absolute inset-0 pointer-events-none" data-testid="fractal-trees-bg">
      <FractalTrees />
    </div>
    <div className="container-ms relative w-full py-20 md:py-28 text-center z-[2]">
      <div className="flex justify-center mb-8 md:mb-10" style={{ color: "var(--copper)" }}>
        <SigilQuadrature size={44} />
      </div>
      <h2 className="font-serif text-[34px] sm:text-[48px] md:text-[60px] leading-[1.02] max-w-[760px] mx-auto mb-8 md:mb-10">
        Сегодня ночью<br/>что-то приснится.
      </h2>
      <a href={APP_URL} className="btn-copper" data-testid="final-cta-open-app">
        Открыть приложение
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <path d="M2 7 H12 M8 3 L12 7 L8 11" stroke="currentColor" strokeWidth="1.2" />
        </svg>
      </a>
      <div className="mt-6 md:mt-7 text-[12px] md:text-[13px] px-4" style={{ color: "var(--stone)" }}>
        Канал автора{" "}
        <a href={TG_URL} target="_blank" rel="noreferrer" style={{ color: "var(--cream-dim)" }} className="hover:underline" data-testid="final-tg-link">
          @CyberCore
        </a>{" "}
        — про снотолкование, бессознательное и киберпанк.
      </div>
    </div>
  </SectionFrame>
);

const Footer = () => (
  <footer className="relative border-t hairline" data-testid="site-footer">
    <div className="container-ms py-10 flex flex-col md:flex-row gap-6 md:items-center md:justify-between">
      <div className="text-[11px] md:text-[12px] tracking-[0.18em] uppercase" style={{ color: "var(--stone)" }}>
        © 2026 · innerCore
      </div>
      <div className="flex items-center gap-5 md:gap-7 text-[12px] md:text-[13px] flex-wrap" style={{ color: "var(--stone)" }}>
        <a href="mailto:hi@innercore.art" className="hover:text-[color:var(--cream)]" style={{ color: "inherit", textDecoration: "none" }} data-testid="footer-contact">
          контакт
        </a>
        <a href="#privacy" className="hover:text-[color:var(--cream)]" style={{ color: "inherit", textDecoration: "none" }} data-testid="footer-privacy">
          политика приватности
        </a>
        <a href={TG_URL} target="_blank" rel="noreferrer" className="hover:text-[color:var(--cream)]" style={{ color: "inherit", textDecoration: "none" }} data-testid="footer-telegram">
          telegram
        </a>
      </div>
      <div style={{ color: "var(--copper)" }} className="md:ml-auto">
        <FooterSeal size={26} />
      </div>
    </div>
  </footer>
);

function App() {
  useFadeIn();
  return (
    <div className="App relative" data-testid="app-root">
      <Nav />
      <main>
        <Hero />
        <WhatItIs />
        <HowItWorks />
        <MapSection />
        <Privacy />
        <DeepBlock />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}

export default App;
