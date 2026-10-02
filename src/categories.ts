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
