import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';

export const GET: APIRoute = async () => {
	const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000);

	const allPosts = await getCollection('blog');
	const recentPosts = allPosts.filter((post) => post.data.pubDate >= twoDaysAgo);

	const urls = recentPosts
		.map((post) => {
			const lang = post.id.startsWith('en/') ? 'en' : 'es';
			const slug = post.id.replace(/^(es|en)\//, '');
			const url = `https://colombiaforce.com/${lang}/blog/${slug}/`;
			const pubDate = post.data.pubDate.toISOString();

			return `  <url>
    <loc>${url}</loc>
    <news:news>
      <news:publication>
        <news:name>Colombia Force</news:name>
        <news:language>${lang}</news:language>
      </news:publication>
      <news:publication_date>${pubDate}</news:publication_date>
      <news:title><![CDATA[${post.data.title}]]></news:title>
    </news:news>
  </url>`;
		})
		.join('\n');

	const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
${urls}
</urlset>`;

	return new Response(xml, {
		headers: { 'Content-Type': 'application/xml' },
	});
};
