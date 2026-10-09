// @ts-check

import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig, fontProviders } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://colombiaforce.com',
  redirects: {
    '/politica-editorial': '/es/politica-editorial',
    '/contacto': '/es/contacto',
    '/privacidad': '/es/privacidad',
    '/en/politica-editorial': '/en/editorial-policy',
    '/en/contacto': '/en/contact',
    '/en/privacidad': '/en/privacy',
    '/en/categoria/operativos': '/en/category/operations',
    '/en/categoria/incautaciones': '/en/category/seizures',
    '/en/categoria/sometimientos': '/en/category/surrenders',
    '/en/categoria/bajas': '/en/category/casualties',
  },
  i18n: {
    locales: ['es', 'en'],
    defaultLocale: 'es',
    routing: {
      prefixDefaultLocale: true,
    },
  },
  integrations: [mdx(), sitemap()],
  fonts: [
    {
      provider: fontProviders.local(),
      name: 'Atkinson',
      cssVariable: '--font-atkinson',
      fallbacks: ['sans-serif'],
      options: {
        variants: [
          {
            src: ['./src/assets/fonts/atkinson-regular.woff'],
            weight: 400,
            style: 'normal',
            display: 'swap',
          },
          {
            src: ['./src/assets/fonts/atkinson-bold.woff'],
            weight: 700,
            style: 'normal',
            display: 'swap',
          },
        ],
      },
    },
  ],
});
