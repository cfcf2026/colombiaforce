import { getCollection } from 'astro:content';
import { CATEGORY_SLUGS, CATEGORY_URL_SLUGS, type CategorySlug } from '../categories';

export type Lang = 'es' | 'en';
const otherLang = (l: Lang): Lang => (l === 'es' ? 'en' : 'es');

export const PAGE_SLUGS = {
	es: { editorial: 'politica-editorial', contact: 'contacto', privacy: 'privacidad' },
	en: { editorial: 'editorial-policy', contact: 'contact', privacy: 'privacy' },
} as const;
type PageKey = keyof typeof PAGE_SLUGS.es;

export const CATEGORY_SEGMENT = { es: 'categoria', en: 'category' } as const;

type PostLike = { id: string; data: { urlSlug?: string } };

// Dirección de una nota: usa "urlSlug" si existe; si no, el nombre del archivo.
export function postSlug(post: PostLike): string {
	return post.data.urlSlug ?? post.id.replace(/^(es|en)\//, '');
}
export function postPath(lang: Lang, post: PostLike): string {
	return `/${lang}/blog/${postSlug(post)}/`;
}
export function categoryPath(lang: Lang, cat: string): string {
	const slug = CATEGORY_URL_SLUGS[lang][cat as CategorySlug] ?? cat;
	return `/${lang}/${CATEGORY_SEGMENT[lang]}/${slug}`;
}
export function pagePath(lang: Lang, key: PageKey): string {
	return `/${lang}/${PAGE_SLUGS[lang][key]}`;
}

// Devuelve la dirección de la misma página en cada idioma.
// paired = false si la página no tiene versión en el otro idioma.
export async function getAlternates(pathname: string) {
	const m = pathname.match(/^\/(es|en)(\/.*)?$/);
	if (!m) return { es: '/es/', en: '/en/', paired: false };

	const lang = m[1] as Lang;
	const to = otherLang(lang);
	const rest = m[2] ?? '';
	const seg = rest.split('/').filter(Boolean);
	const tail = pathname.length > 1 && pathname.endsWith('/') ? '/' : '';

	let restTo = rest.replace(/\/+$/, '');
	let paired = true;

	if (seg.length === 1) {
		const key = (Object.keys(PAGE_SLUGS[lang]) as PageKey[]).find(
			(k) => PAGE_SLUGS[lang][k] === seg[0],
		);
		if (key) restTo = '/' + PAGE_SLUGS[to][key];
	} else if (seg.length === 2 && seg[0] === CATEGORY_SEGMENT[lang]) {
		const cat = CATEGORY_SLUGS.find((c) => CATEGORY_URL_SLUGS[lang][c] === seg[1]);
		if (cat) restTo = `/${CATEGORY_SEGMENT[to]}/${CATEGORY_URL_SLUGS[to][cat]}`;
	} else if (seg.length === 2 && seg[0] === 'blog') {
		const posts = await getCollection('blog');
		const current = posts.find((p) => p.id.startsWith(`${lang}/`) && postSlug(p) === seg[1]);
		const file = current?.id.replace(/^(es|en)\//, '');
		const twin = file ? posts.find((p) => p.id === `${to}/${file}`) : undefined;
		if (twin) {
			restTo = `/blog/${postSlug(twin)}`;
		} else {
			restTo = '';
			paired = false;
		}
	}

	return {
		[lang]: pathname,
		[to]: `/${to}${restTo}${tail}`,
		paired,
	} as { es: string; en: string; paired: boolean };
}
