import React, { useEffect, useState } from "react";
import "@/App.css";
import { Menu, X, Plus } from "lucide-react";
import Sphere from "@/components/Sphere";
import DreamMap from "@/components/DreamMap";
import { SigilQuadrature, SigilOuroboros, KeyGlyph, FooterSeal } from "@/components/Sigils";
import FractalDots from "@/components/FractalDots";
import FractalTrees from "@/components/FractalTrees";
import { LangProvider, useLang } from "@/LangContext";
import { ARCHETYPES, ARCHETYPES_INTRO, MEMORY_TIPS } from "@/i18n";

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

const LangToggle = ({ small }) => {
  const { lang, setLang } = useLang();
  return (
    <div className={`lang-toggle ${small ? "lang-small" : ""}`} data-testid="lang-toggle">
      <button
        type="button"
        className={lang === "ru" ? "active" : ""}
        aria-pressed={lang === "ru"}
        onClick={() => setLang("ru")}
        data-testid="lang-ru"
      >
        RU
      </button>
      <button
        type="button"
        className={lang === "en" ? "active" : ""}
        aria-pressed={lang === "en"}
        onClick={() => setLang("en")}
        data-testid="lang-en"
      >
        EN
      </button>
    </div>
  );
};

const Nav = () => {
  const { t } = useLang();
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
    { href: "#manifest", label: t.nav.manifest, testid: "nav-manifest" },
    { href: "#how", label: t.nav.how, testid: "nav-how" },
    { href: "#map", label: t.nav.map, testid: "nav-map" },
    { href: "#reading", label: t.nav.reading, testid: "nav-reading" },
    { href: "#pricing", label: t.nav.pricing, testid: "nav-pricing" },
    { href: "#faq", label: t.nav.faq, testid: "nav-faq" },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? "nav-scrolled" : ""}`}
      data-testid="site-nav"
    >
      <nav className="container-ms py-4 md:py-5 flex items-center justify-between gap-4">
        <a href="#top" onClick={close} className="flex items-center gap-3 no-underline shrink-0" data-testid="brand-mark">
          <span style={{ color: "var(--copper)" }}>
            <SigilQuadrature size={22} />
          </span>
          <span className="font-serif text-[19px] md:text-[20px] tracking-[0.02em]" style={{ color: "var(--cream)" }}>
            innerCore
          </span>
        </a>

        <div className="hidden md:flex items-center gap-6 lg:gap-8 text-[14px]" style={{ color: "var(--stone)" }}>
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

        <div className="hidden md:flex items-center gap-4">
          <LangToggle />
          <a href={APP_URL} className="btn-ghost" data-testid="nav-cta">{t.nav.cta}</a>
        </div>

        <button
          className="md:hidden p-2 -mr-2 text-[color:var(--cream)]"
          aria-label={open ? "close" : "open"}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          data-testid="mobile-menu-toggle"
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>

      <div
        className={`md:hidden overflow-hidden transition-all duration-300 ${open ? "max-h-[640px] opacity-100" : "max-h-0 opacity-0"}`}
        data-testid="mobile-menu"
        style={{ background: "rgba(15, 17, 24, 0.97)", borderTop: open ? "1px solid var(--hairline)" : "none" }}
      >
        <div className="container-ms py-6 flex flex-col gap-5">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={close}
              className="font-serif text-[23px]"
              style={{ color: "var(--cream)", textDecoration: "none" }}
              data-testid={`m-${l.testid}`}
            >
              {l.label}
            </a>
          ))}
          <div className="pt-2"><LangToggle /></div>
          <a href={APP_URL} onClick={close} className="btn-copper mt-2 self-start" data-testid="mobile-cta">
            {t.hero.cta}
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M2 7 H12 M8 3 L12 7 L8 11" stroke="currentColor" strokeWidth="1.2" />
            </svg>
          </a>
        </div>
      </div>
    </header>
  );
};

const Section = ({ id, children, bg = "ink", className = "", testid }) => (
  <section
    id={id}
    className={`relative overflow-hidden min-h-screen bg-${bg} ${className}`}
    data-testid={testid}
  >
    {children}
  </section>
);

const Hero = () => {
  const { t } = useLang();
  return (
    <Section id="top" bg="ink" className="flex items-center" testid="hero-section">
      <div className="container-ms w-full pt-28 md:pt-24 pb-12 md:pb-16">
        <div className="grid md:grid-cols-12 gap-10 md:gap-8 items-center">
          <div className="relative order-2 md:order-1 md:col-span-7">
            <div className="flex items-center gap-3 mb-6 md:mb-7" style={{ color: "var(--stone)" }}>
              <span style={{ color: "var(--copper)" }}>
                <SigilOuroboros size={38} />
              </span>
              <span className="text-[11px] md:text-[12px] tracking-[0.32em] uppercase">{t.hero.kicker}</span>
            </div>
            <h1
              className="font-serif text-[35px] sm:text-[47px] md:text-[59px] lg:text-[65px] leading-[1.02] tracking-[-0.015em] max-w-[760px]"
              data-testid="hero-title"
            >
              {t.hero.title1}{" "}
              <span style={{ color: "var(--copper)" }}>{t.hero.title2}</span>
            </h1>
            <p className="mt-6 md:mt-8 max-w-[520px] text-[17px] md:text-[19px]" style={{ color: "var(--cream-dim)" }} data-testid="hero-subtitle">
              {t.hero.subtitle}
            </p>
            <div className="mt-8 md:mt-10 flex items-center gap-5 md:gap-6 flex-wrap">
              <a href={APP_URL} className="btn-copper" data-testid="hero-cta-open-app">
                {t.hero.cta}
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M2 7 H12 M8 3 L12 7 L8 11" stroke="currentColor" strokeWidth="1.2" />
                </svg>
              </a>
              <a
                href="#manifest"
                className="text-[13px] md:text-[14px] tracking-[0.12em] uppercase hover:underline"
                style={{ color: "var(--stone)", textDecoration: "none" }}
                data-testid="hero-scroll-down"
              >
                {t.hero.scroll}
              </a>
            </div>

            <div className="mt-10 md:mt-14 flex items-center gap-3 md:gap-6 text-[12px] md:text-[13px] flex-wrap" style={{ color: "var(--stone)" }}>
              {t.hero.badges.map((b, i) => (
                <React.Fragment key={i}>
                  {i === 0 ? (
                    <span className="flex items-center gap-2">
                      <span className="w-1 h-1 rounded-full" style={{ background: "var(--copper)" }}></span>
                      {b}
                    </span>
                  ) : (
                    <span className={i === 3 ? "hidden sm:inline" : ""}>{b}</span>
                  )}
                  {i < t.hero.badges.length - 1 && <span className={i === 2 ? "hidden sm:inline" : ""}>·</span>}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="relative order-1 md:order-2 md:col-span-5 max-w-[420px] md:max-w-none mx-auto w-full" data-testid="hero-sphere">
            <Sphere />
            <div className="mt-2 text-center font-serif italic text-[13px] md:text-[15px] px-4" style={{ color: "var(--stone)" }}>
              {t.hero.caption}
            </div>
          </div>
        </div>
      </div>
    </Section>
  );
};

const renderParagraph = (p, idx) => {
  if (typeof p === "string") {
    return <p key={idx}>{p}</p>;
  }
  if (p && p.italic) {
    return (
      <p key={idx} className="font-serif italic" style={{ color: "var(--cream)" }}>
        {p.italic}
      </p>
    );
  }
  return null;
};

const SubBlock = ({ block, i }) => (
  <div className="mb-14 md:mb-20 max-w-[720px]" data-testid={`manifest-block-${i}`}>
    {block.kicker && (
      <div className="text-[11px] md:text-[12px] tracking-[0.32em] uppercase mb-4" style={{ color: "var(--copper)" }}>
        {block.kicker}
      </div>
    )}
    {block.title && (
      <h3 className="font-serif text-[25px] sm:text-[31px] md:text-[37px] leading-[1.15] mb-5 md:mb-6" style={{ color: "var(--cream)" }}>
        {block.title}
      </h3>
    )}
    <div className="space-y-4 md:space-y-5 text-[16px] md:text-[18px]" style={{ color: "var(--cream-dim)" }}>
      {block.paragraphs.map(renderParagraph)}
    </div>
  </div>
);

const Manifesto = () => {
  const { t } = useLang();
  return (
    <Section id="manifest" bg="ink-soft" className="fade-in" testid="section-manifest">
      <div className="absolute inset-0 pointer-events-none" data-testid="fractal-bg-manifest">
        <FractalDots variant="copper" density={110} opacity={1} />
      </div>
      <div className="container-ms relative w-full py-24 md:py-32 z-[2]">
        <div className="mb-14 md:mb-20 max-w-[820px]">
          <div className="text-[11px] md:text-[12px] tracking-[0.32em] uppercase mb-6" style={{ color: "var(--copper)" }}>
            {t.manifest.kicker}
          </div>
          <h2
            className="font-serif text-[33px] sm:text-[45px] md:text-[59px] leading-[1.04] tracking-[-0.01em]"
            data-testid="manifest-title"
          >
            {t.manifest.title}
          </h2>
        </div>

        {t.manifest.blocks.map((b, i) => (
          <SubBlock key={i} block={b} i={i} />
        ))}
      </div>
    </Section>
  );
};

const Tool = () => {
  const { t } = useLang();
  return (
    <Section id="how" bg="ink" className="flex items-center fade-in" testid="section-how">
      <div className="absolute inset-0 pointer-events-none" data-testid="fractal-trees-bg-how">
        <FractalTrees />
      </div>
      <div className="container-ms relative w-full py-24 md:py-32 z-[2]">
        <div className="flex items-baseline justify-between mb-12 md:mb-16 flex-wrap gap-4">
          <div>
            <div className="text-[11px] md:text-[12px] tracking-[0.32em] uppercase mb-4" style={{ color: "var(--copper)" }}>
              {t.tool.kicker}
            </div>
            <h2 className="font-serif text-[33px] sm:text-[45px] md:text-[57px] leading-[1.02]" data-testid="how-title">
              {t.tool.titleA}<br/>{t.tool.titleB}
            </h2>
          </div>
          <div className="text-[11px] md:text-[13px] tracking-[0.32em] uppercase font-serif italic" style={{ color: "var(--stone)" }}>
            {t.tool.subkicker}
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-px" style={{ background: "var(--hairline)" }}>
          {t.tool.cards.map((c, i) => (
            <div key={i} className="card-ms" data-testid={`how-card-${i}`} style={{ borderRadius: 0, borderWidth: 0, background: "rgba(15, 17, 24, 0.78)", backdropFilter: "blur(8px)" }}>
              <div className="flex items-center justify-between mb-6 md:mb-8">
                <span className="glyph">{c.glyph}</span>
                <span className="text-[11px] tracking-[0.32em] uppercase" style={{ color: "var(--stone)" }}>
                  {String(i + 1).padStart(2, "0")} · {c.label}
                </span>
              </div>
              <h3 className="font-serif text-[27px] md:text-[31px] mb-4">{c.title}</h3>
              <p className="text-[16px] md:text-[17px] mb-4 font-serif italic" style={{ color: "var(--cream)" }}>{c.intro}</p>
              <p className="text-[15px] md:text-[16px]" style={{ color: "var(--cream-dim)" }}>{c.body}</p>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
};

const MapAndPrivacy = () => {
  const { t } = useLang();
  return (
    <Section id="map" bg="ink-soft" className="fade-in" testid="section-map">
      <div className="absolute inset-0 pointer-events-none" data-testid="fractal-bg-map">
        <FractalDots variant="cinnabar" density={120} opacity={0.95} />
      </div>
      <div className="container-ms relative w-full py-24 md:py-32 z-[2]">
        <div className="grid md:grid-cols-12 gap-10 md:gap-12 items-start">
          <div className="md:col-span-5">
            <div className="text-[11px] md:text-[12px] tracking-[0.32em] uppercase mb-5" style={{ color: "var(--copper)" }}>
              {t.map.kicker}
            </div>
            <h2 className="font-serif text-[33px] sm:text-[45px] md:text-[53px] leading-[1.04] mb-6">
              {t.map.title}
            </h2>
            <p className="text-[16px] md:text-[18px] mb-4" style={{ color: "var(--cream-dim)" }}>
              {t.map.p1}
            </p>
            <p className="text-[15px] md:text-[16px] italic font-serif" style={{ color: "var(--stone)" }}>
              {t.map.p2}
            </p>
          </div>
          <div className="md:col-span-7" data-testid="dream-map-demo">
            <DreamMap />
          </div>
        </div>

        <div id="sigillum" className="mt-20 md:mt-28 grid md:grid-cols-12 gap-8 md:gap-12 items-start max-w-[1100px]" data-testid="block-privacy">
          <div className="md:col-span-3 flex md:justify-end">
            <div style={{ color: "var(--copper)" }}>
              <KeyGlyph size={60} />
            </div>
          </div>
          <div className="md:col-span-9">
            <div className="text-[11px] md:text-[12px] tracking-[0.32em] uppercase mb-4" style={{ color: "var(--copper)" }}>
              {t.sigillum.kicker}
            </div>
            <h3 className="font-serif text-[29px] sm:text-[37px] md:text-[43px] leading-[1.08] mb-6">
              {t.sigillum.titleA}<br className="hidden md:inline" /> {t.sigillum.titleB}
            </h3>
            <p className="text-[16px] md:text-[18px] mb-4 max-w-[640px]" style={{ color: "var(--cream-dim)" }}>
              {t.sigillum.p1}
            </p>
            <p className="text-[15px] md:text-[16px] italic font-serif max-w-[620px]" style={{ color: "var(--stone)" }}>
              {t.sigillum.p2}
            </p>
          </div>
        </div>
      </div>
    </Section>
  );
};

const ArchetypesInline = ({ lang }) => (
  <p>
    {ARCHETYPES_INTRO[lang]}{" "}
    {ARCHETYPES[lang].map((a, i) => (
      <React.Fragment key={i}>
        <span className="font-serif italic" style={{ color: "var(--cream)" }}>{a}</span>
        {i < ARCHETYPES[lang].length - 1 ? ", " : "."}
      </React.Fragment>
    ))}
  </p>
);

const MemoryTipsInline = ({ lang }) => (
  <p>
    {MEMORY_TIPS[lang].map((m, i) => (
      <React.Fragment key={i}>
        <span className="font-serif italic" style={{ color: "var(--cream)" }}>{m.label}</span>{" "}
        {m.text}{" "}
      </React.Fragment>
    ))}
  </p>
);

const renderArticleParagraph = (p, idx, lang) => {
  if (typeof p === "string") return <p key={idx}>{p}</p>;
  if (p.kind === "archetypes-ru" || p.kind === "archetypes-en")
    return <ArchetypesInline key={idx} lang={lang} />;
  if (p.kind === "memory-tips-ru" || p.kind === "memory-tips-en")
    return <MemoryTipsInline key={idx} lang={lang} />;
  return null;
};

const ReadingArticle = ({ article, lang, i }) => (
  <article className="mb-16 md:mb-20 max-w-[720px]" data-testid={`reading-article-${i}`}>
    <div className="text-[11px] md:text-[12px] tracking-[0.32em] uppercase mb-3" style={{ color: "var(--copper)" }}>
      {article.kicker}
    </div>
    <h3 className="font-serif text-[25px] sm:text-[31px] md:text-[35px] leading-[1.18] mb-5 md:mb-6" style={{ color: "var(--cream)" }}>
      {article.title}
    </h3>
    <div className="space-y-4 text-[16px] md:text-[17px] leading-[1.75]" style={{ color: "var(--cream-dim)" }}>
      {article.paragraphs.map((p, idx) => renderArticleParagraph(p, idx, lang))}
    </div>
  </article>
);

const Reading = () => {
  const { t, lang } = useLang();
  return (
    <Section id="reading" bg="ink" className="fade-in" testid="section-reading">
      <div className="container-ms w-full py-24 md:py-32">
        <div className="mb-14 md:mb-20 max-w-[820px]">
          <div className="text-[11px] md:text-[12px] tracking-[0.32em] uppercase mb-6" style={{ color: "var(--copper)" }}>
            {t.reading.kicker}
          </div>
          <h2 className="font-serif text-[33px] sm:text-[45px] md:text-[57px] leading-[1.04] tracking-[-0.01em]">
            {t.reading.title}
          </h2>
          <p className="mt-5 text-[16px] md:text-[17px] italic font-serif max-w-[620px]" style={{ color: "var(--stone)" }}>
            {t.reading.lead}
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-x-10 md:gap-x-14 gap-y-0 md:gap-y-4">
          {t.reading.articles.map((a, i) => (
            <ReadingArticle key={i} article={a} lang={lang} i={i} />
          ))}
        </div>
      </div>
    </Section>
  );
};

const renderFaqAnswer = (a, idx, lang) => {
  if (typeof a === "string") return <p key={idx}>{a}</p>;
  if (a.kind === "memory-tips-ru" || a.kind === "memory-tips-en")
    return <MemoryTipsInline key={idx} lang={lang} />;
  return null;
};

const FAQItem = ({ q, a, lang, i }) => (
  <details className="faq-item border-b hairline py-6 md:py-7" data-testid={`faq-item-${i}`}>
    <summary className="flex items-start justify-between gap-6 cursor-pointer group">
      <h3 className="font-serif text-[20px] sm:text-[23px] md:text-[27px] leading-[1.25]" style={{ color: "var(--cream)" }}>
        {q}
      </h3>
      <span className="shrink-0 mt-1" style={{ color: "var(--copper)" }} aria-hidden="true">
        <Plus size={22} className="faq-plus transition-transform duration-300" />
      </span>
    </summary>
    <div className="mt-5 max-w-[640px] space-y-3 md:space-y-4 text-[16px] md:text-[17px] leading-[1.75]" style={{ color: "var(--cream-dim)" }}>
      {a.map((p, idx) => renderFaqAnswer(p, idx, lang))}
    </div>
  </details>
);

const PricingSection = () => {
  const { lang } = useLang();
  const isRu = lang === 'ru';

  const features = isRu
    ? [
        { label: 'Free', items: ['До 5 записей в день', 'Дневник снов', 'Базовый анализ'] },
        { label: 'Pro', items: ['Без лимитов', 'Глубокий анализ Юнга', 'Карта снов', 'Приоритетная обработка'] },
      ]
    : [
        { label: 'Free', items: ['Up to 5 entries per day', 'Dream journal', 'Basic analysis'] },
        { label: 'Pro', items: ['Unlimited entries', 'Deep Jungian analysis', 'Dream map', 'Priority processing'] },
      ];

  return (
    <Section id="pricing" bg="ink" className="fade-in" testid="section-pricing">
      <div className="container-ms w-full py-24 md:py-32">
        <div className="mb-12 md:mb-16 max-w-[820px]">
          <div className="text-[11px] md:text-[12px] tracking-[0.32em] uppercase mb-6" style={{ color: 'var(--copper)' }}>
            {isRu ? 'Тарифы' : 'Pricing'}
          </div>
          <h2 className="font-serif text-[33px] sm:text-[45px] md:text-[57px] leading-[1.04] tracking-[-0.01em]">
            {isRu ? '14 дней Pro в подарок' : '14 days of Pro on us'}
          </h2>
          <p className="mt-5 text-[16px] md:text-[18px] max-w-[640px]" style={{ color: 'var(--cream-dim)' }}>
            {isRu
              ? 'Регистрируешься — получаешь 14 дней безлимитного Pro. Дальше Free или подписка, выбор за тобой.'
              : 'Sign up and you get 14 days of unlimited Pro. After that — Free or a subscription, your call.'}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-5 max-w-[640px]">
          {features.map((tier) => (
            <div
              key={tier.label}
              className="rounded-[2px] px-5 py-6"
              style={{
                background: tier.label === 'Pro' ? 'rgba(184, 115, 51, 0.08)' : 'rgba(232, 225, 212, 0.03)',
                border: `1px solid ${tier.label === 'Pro' ? 'var(--copper)' : 'var(--hairline)'}`,
              }}
            >
              <div
                className="text-[11px] tracking-[0.22em] uppercase mb-4"
                style={{ color: tier.label === 'Pro' ? 'var(--copper)' : 'var(--stone)' }}
              >
                {tier.label}
              </div>
              <ul className="space-y-2">
                {tier.items.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-[14px] md:text-[15px]" style={{ color: 'var(--cream-dim)' }}>
                    <span style={{ color: 'var(--copper)', lineHeight: '1.6' }}>·</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-col items-start gap-3">
          <a href={APP_URL} className="btn-copper" data-testid="pricing-subscribe-cta">
            {isRu ? 'Начать бесплатно' : 'Start for free'}
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M2 7 H12 M8 3 L12 7 L8 11" stroke="currentColor" strokeWidth="1.2" />
            </svg>
          </a>
          <div className="text-[12px] tracking-[0.04em]" style={{ color: 'var(--stone)' }}>
            {isRu ? 'Никаких автосписаний без твоего подтверждения.' : 'No silent auto-charges — ever.'}
          </div>
        </div>
      </div>
    </Section>
  );
};

const FAQSection = () => {
  const { t, lang } = useLang();
  return (
    <Section id="faq" bg="ink-soft" className="fade-in" testid="section-faq">
      <div className="container-ms w-full py-24 md:py-32">
        <div className="mb-12 md:mb-16 max-w-[820px]">
          <div className="text-[11px] md:text-[12px] tracking-[0.32em] uppercase mb-6" style={{ color: "var(--copper)" }}>
            {t.faq.kicker}
          </div>
          <h2 className="font-serif text-[33px] sm:text-[45px] md:text-[57px] leading-[1.04] tracking-[-0.01em]">
            {t.faq.title}
          </h2>
        </div>
        <div className="max-w-[860px] border-t hairline">
          {t.faq.items.map((it, i) => (
            <FAQItem key={i} i={i} q={it.q} a={it.a} lang={lang} />
          ))}
        </div>
      </div>
    </Section>
  );
};

const FinalCTA = () => {
  const { t } = useLang();
  return (
    <Section id="final" bg="ink" className="flex items-center fade-in" testid="section-final-cta">
      <div className="absolute inset-0 pointer-events-none" data-testid="fractal-trees-bg">
        <FractalTrees />
      </div>
      <div className="container-ms relative w-full py-24 md:py-32 text-center z-[2]">
        <div className="flex justify-center mb-8 md:mb-10" style={{ color: "var(--copper)" }}>
          <SigilQuadrature size={44} />
        </div>
        <h2 className="font-serif text-[35px] sm:text-[49px] md:text-[61px] leading-[1.02] max-w-[760px] mx-auto mb-8 md:mb-10">
          {t.final.titleA}<br/>{t.final.titleB}
        </h2>
        <a href={APP_URL} className="btn-copper" data-testid="final-cta-open-app">
          {t.final.cta}
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M2 7 H12 M8 3 L12 7 L8 11" stroke="currentColor" strokeWidth="1.2" />
          </svg>
        </a>
        <div className="mt-6 md:mt-7 text-[13px] md:text-[14px] px-4" style={{ color: "var(--stone)" }}>
          {t.final.tgLead}{" "}
          <a href={TG_URL} target="_blank" rel="noreferrer" style={{ color: "var(--cream-dim)" }} className="hover:underline" data-testid="final-tg-link">
            @CyberCore
          </a>{" "}
          {t.final.tgTail}
        </div>
      </div>
    </Section>
  );
};

const Footer = () => {
  const { t } = useLang();
  return (
    <footer className="relative border-t hairline bg-ink" data-testid="site-footer">
      <div className="container-ms py-10 flex flex-col md:flex-row gap-6 md:items-center md:justify-between">
        <div className="text-[12px] md:text-[13px] tracking-[0.18em] uppercase" style={{ color: "var(--stone)" }}>
          © 2026 · innerCore
        </div>
        <div className="flex items-center gap-5 md:gap-7 text-[13px] md:text-[14px] flex-wrap" style={{ color: "var(--stone)" }}>
          <a href="mailto:hi@innercore.art" className="hover:text-[color:var(--cream)]" style={{ color: "inherit", textDecoration: "none" }} data-testid="footer-contact">
            {t.footer.contact}
          </a>
          <a href="#sigillum" className="hover:text-[color:var(--cream)]" style={{ color: "inherit", textDecoration: "none" }} data-testid="footer-privacy">
            {t.footer.privacy}
          </a>
          <a href={TG_URL} target="_blank" rel="noreferrer" className="hover:text-[color:var(--cream)]" style={{ color: "inherit", textDecoration: "none" }} data-testid="footer-telegram">
            {t.footer.telegram}
          </a>
        </div>
        <div style={{ color: "var(--copper)" }} className="md:ml-auto">
          <FooterSeal size={26} />
        </div>
      </div>
    </footer>
  );
};

function AppInner() {
  useFadeIn();
  return (
    <div className="App relative" data-testid="app-root">
      <Nav />
      <main>
        <Hero />
        <Manifesto />
        <Tool />
        <MapAndPrivacy />
        <Reading />
        <PricingSection />
        <FAQSection />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <LangProvider>
      <AppInner />
    </LangProvider>
  );
}
