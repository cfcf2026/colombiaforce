export const languages = {
	es: 'Español',
	en: 'English',
};

export const defaultLang = 'es';

export const ui = {
	es: {
		'nav.home': 'Inicio',
		'nav.blog': 'Blog',
		'nav.about': 'Nosotros',
		'cat.operativos': 'Operativos',
		'cat.incautaciones': 'Incautaciones',
		'cat.capturados': 'Capturados',
		'cat.bajas': 'Bajas',
		'cat.otros': 'Otros',
	},
	en: {
		'nav.home': 'Home',
		'nav.blog': 'Blog',
		'nav.about': 'About',
		'cat.operativos': 'Operations',
		'cat.incautaciones': 'Seizures',
		'cat.capturados': 'Arrests',
		'cat.bajas': 'Casualties',
		'cat.otros': 'Other',
	},
} as const;

export function getLangFromUrl(url: URL) {
	const [, lang] = url.pathname.split('/');
	if (lang === 'en') return 'en';
	return defaultLang;
}

export function useTranslations(lang: 'es' | 'en') {
	return function t(key: keyof (typeof ui)['es']) {
		return ui[lang][key] ?? ui[defaultLang][key];
	};
}
