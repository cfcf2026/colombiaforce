export const CATEGORY_SLUGS = ['operativos', 'incautaciones', 'capturados', 'bajas', 'otros'] as const;

export const CATEGORY_LABELS = {
	es: {
		operativos: 'Operativos',
		incautaciones: 'Incautaciones',
		capturados: 'Capturados',
		bajas: 'Bajas',
		otros: 'Otros',
	},
	en: {
		operativos: 'Operations',
		incautaciones: 'Seizures',
		capturados: 'Arrests',
		bajas: 'Casualties',
		otros: 'Other',
	},
} as const;

export type CategorySlug = (typeof CATEGORY_SLUGS)[number];

export const CATEGORY_URL_SLUGS = {
	es: { operativos: 'operativos', incautaciones: 'incautaciones', capturados: 'capturados', bajas: 'bajas', otros: 'otros' },
	en: { operativos: 'operations', incautaciones: 'seizures', capturados: 'arrests', bajas: 'casualties', otros: 'other' },
} as const;
