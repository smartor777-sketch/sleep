import { useApp } from '../lib/store';
import { t } from '../lib/i18n';
import { Github, Send, ExternalLink, Sparkles } from 'lucide-react';

export default function AboutPage() {
  const lang = useApp((s) => s.lang);

  return (
    <div className="space-y-6 max-w-3xl" data-testid="about-page">
      <section>
        <div className="inline-flex items-center gap-2 muted-text text-xs uppercase tracking-[0.18em] mb-3">
          <Sparkles className="w-4 h-4" />
          {lang === 'ru' ? 'О проекте' : 'About'}
        </div>
        <h1 className="font-display text-3xl sm:text-4xl leading-tight">
          InnerCore — {lang === 'ru' ? 'атлас бессознательного' : 'atlas of the unconscious'}
        </h1>
        <p className="muted-text text-base mt-3">
          {lang === 'ru'
            ? 'AI-дневник снов с юнгианским анализом, контекстным чатом и символической Картой снов.'
            : 'AI dream journal with Jungian analysis, contextual chat and symbolic Dream Map.'}
        </p>
      </section>

      <section className="card-surface rounded-3xl p-5 sm:p-6 space-y-4">
        <h2 className="font-display text-xl">{lang === 'ru' ? 'Что это' : 'What it is'}</h2>
        <p className="text-sm leading-relaxed muted-text">
          {lang === 'ru'
            ? 'Вы записываете сон текстом или голосом — InnerCore анализирует образы, архетипы и символы, ведёт диалог о сне, строит Карту связей и запоминает контекст вашей жизни для более точных интерпретаций. Проект вырос из оригинального InnerCore (core-euler) и развивается как открытый форк.'
            : 'You record a dream via text or voice — InnerCore analyzes images, archetypes and symbols, chats about the dream, builds a Map of connections and remembers your life context for deeper interpretations. The project grew from the original InnerCore (core-euler) and continues as an open fork.'}
        </p>
        <ul className="list-disc list-inside text-sm muted-text space-y-1">
          <li>{lang === 'ru' ? 'Анализ снов на LLM (Gonka / OpenAI-compatible)' : 'LLM dream analysis (Gonka / OpenAI-compatible)'}</li>
          <li>{lang === 'ru' ? 'Карта символов с фильтрами по архетипам' : 'Symbol Map with archetype filters'}</li>
          <li>{lang === 'ru' ? 'Поиск по снам: смысловой + лексический' : 'Dream search: semantic + lexical'}</li>
          <li>{lang === 'ru' ? 'Память и эволюционирующий портрет психики' : 'Memory and evolving psyche portrait'}</li>
        </ul>
      </section>

      <section className="card-surface rounded-3xl p-5 sm:p-6 space-y-4" data-testid="about-links">
        <h2 className="font-display text-xl">{lang === 'ru' ? 'Ссылки и контакты' : 'Links & contacts'}</h2>

        <div className="space-y-3 text-sm">
          <div>
            <div className="font-medium">{lang === 'ru' ? 'Данный форк (sleep)' : 'This fork (sleep)'}</div>
            <div className="flex flex-wrap gap-3 mt-1">
              <a
                href="https://github.com/smartor777-sketch/sleep"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 accent-text hover:underline"
                data-testid="about-github-fork"
              >
                <Github className="w-4 h-4" /> github.com/smartor777-sketch/sleep <ExternalLink className="w-3 h-3" />
              </a>
              <a
                href="https://t.me/Latinosaur"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 accent-text hover:underline"
                data-testid="about-telegram-fork"
              >
                <Send className="w-4 h-4" /> @Latinosaur
              </a>
            </div>
          </div>

          <div className="h-px divider border-t" />

          <div>
            <div className="font-medium">{lang === 'ru' ? 'Оригинальная версия InnerCore' : 'Original InnerCore'}</div>
            <div className="flex flex-wrap gap-3 mt-1 muted-text">
              <a href="https://github.com/core-euler" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 hover:accent-text hover:underline" data-testid="about-github-orig">
                <Github className="w-4 h-4" /> core-euler
              </a>
              <a href="https://t.me/CoreEuler" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 hover:accent-text hover:underline" data-testid="about-telegram-orig">
                <Send className="w-4 h-4" /> @CoreEuler
              </a>
            </div>
            <p className="muted-text text-xs mt-1">
              {lang === 'ru' ? 'Контакты выше относятся к оригинальному проекту.' : 'Contacts above belong to the original project.'}
            </p>
          </div>
        </div>
      </section>

      <section className="muted-text text-xs">
        <p>MIT License · InnerCore v0.3</p>
      </section>
    </div>
  );
}
