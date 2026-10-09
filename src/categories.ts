export const CATEGORY_SLUGS = ['operativos', 'incautaciones', 'sometimientos', 'bajas'] as const;

export const CATEGORY_LABELS = {
	es: {
		operativos: 'Operativos',
		incautaciones: 'Incautaciones',
		sometimientos: 'Sometimientos',
		bajas: 'Bajas',
	},
	en: {
		operativos: 'Operations',
		incautaciones: 'Seizures',
		sometimientos: 'Surrenders',
		bajas: 'Casualties',
	},
} as const;

export type CategorySlug = (typeof CATEGORY_SLUGS)[number];

export const CATEGORY_URL_SLUGS = {
	es: { operativos: 'operativos', incautaciones: 'incautaciones', sometimientos: 'sometimientos', bajas: 'bajas' },
	en: { operativos: 'operations', incautaciones: 'seizures', sometimientos: 'surrenders', bajas: 'casualties' },
} as const;
