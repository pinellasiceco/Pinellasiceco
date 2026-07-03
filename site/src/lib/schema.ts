// Schema.org builders. NAP + @id conventions live in BaseLayout; these
// reference the same business entity.
const BUSINESS_ID = 'https://www.pinellasiceco.com/#business';

export function faqSchema(items: { q: string; a: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: items.map((i) => ({
      '@type': 'Question',
      name: i.q,
      acceptedAnswer: { '@type': 'Answer', text: i.a.replace(/<[^>]+>/g, '') },
    })),
  };
}

export function serviceSchema(opts: { name: string; description: string; url: string; serviceType: string }) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Service',
    name: opts.name,
    serviceType: opts.serviceType,
    description: opts.description,
    url: opts.url,
    provider: { '@id': BUSINESS_ID },
    areaServed: [
      { '@type': 'City', name: 'Tampa' },
      { '@type': 'City', name: 'St. Petersburg' },
      { '@type': 'City', name: 'Clearwater' },
      { '@type': 'AdministrativeArea', name: 'Pinellas County' },
      { '@type': 'AdministrativeArea', name: 'Hillsborough County' },
      { '@type': 'AdministrativeArea', name: 'Pasco County' },
    ],
  };
}
