import React from "react";

/** Quadrature of the Circle — alchemical sigil, single-pixel line */
export const SigilQuadrature = ({ size = 38, className = "" }) => (
  <svg
    viewBox="0 0 64 64"
    width={size}
    height={size}
    className={`sigil ${className}`}
    aria-hidden="true"
    fill="none"
    stroke="currentColor"
    strokeWidth="0.7"
  >
    <circle cx="32" cy="32" r="28" />
    <rect x="14" y="14" width="36" height="36" />
    <circle cx="32" cy="32" r="14" />
    <polygon points="32,8 56,50 8,50" />
  </svg>
);

/** Ouroboros — circle-snake, single line */
export const SigilOuroboros = ({ size = 60, className = "" }) => (
  <svg
    viewBox="0 0 64 64"
    width={size}
    height={size}
    className={`sigil ${className}`}
    aria-hidden="true"
    fill="none"
    stroke="currentColor"
    strokeWidth="0.6"
  >
    <circle cx="32" cy="32" r="22" />
    <path d="M32 10 C 44 10 54 20 54 32 C 54 44 44 54 32 54 C 20 54 10 44 10 32 C 10 22 18 14 28 12" />
    <path d="M28 12 L 30 9 M 28 12 L 31 14 M 28 12 L 25 13" />
    <circle cx="32" cy="32" r="2.5" />
  </svg>
);

/** Tiny key icon — geometric */
export const KeyGlyph = ({ size = 40, className = "" }) => (
  <svg
    viewBox="0 0 64 64"
    width={size}
    height={size}
    aria-hidden="true"
    fill="none"
    stroke="currentColor"
    strokeWidth="0.9"
    className={className}
  >
    <circle cx="20" cy="32" r="10" />
    <circle cx="20" cy="32" r="3" />
    <line x1="30" y1="32" x2="54" y2="32" />
    <line x1="44" y1="32" x2="44" y2="40" />
    <line x1="50" y1="32" x2="50" y2="38" />
  </svg>
);

/** Footer corner stamp */
export const FooterSeal = ({ size = 28, className = "" }) => (
  <svg
    viewBox="0 0 64 64"
    width={size}
    height={size}
    aria-hidden="true"
    fill="none"
    stroke="currentColor"
    strokeWidth="0.7"
    className={className}
  >
    <circle cx="32" cy="32" r="26" />
    <circle cx="32" cy="32" r="20" />
    <line x1="32" y1="6" x2="32" y2="58" />
    <line x1="6" y1="32" x2="58" y2="32" />
    <circle cx="32" cy="32" r="3" fill="currentColor" />
  </svg>
);
