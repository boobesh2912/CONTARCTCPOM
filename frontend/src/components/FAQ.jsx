import MarketingLayout from './MarketingLayout';

const faqs = [
  ['Is this a diagnosis tool?', 'No. It is a screening aid and should not replace clinician diagnosis.'],
  ['What audio is best?', 'Quiet environment, stable distance, and 20-30 seconds of natural speech.'],
  ['Is my data saved?', 'Your tests are stored in your account history for trend monitoring.'],
];

const FAQ = () => (
  <MarketingLayout>
    <section className="mx-auto max-w-4xl px-4 py-14 sm:px-6 lg:px-8">
      <h1 className="font-display text-4xl font-bold">FAQ</h1>
      <div className="mt-8 space-y-4">
        {faqs.map(([q, a]) => (
          <article key={q} className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-5 shadow-soft">
            <h3 className="font-display text-xl font-bold">{q}</h3>
            <p className="mt-2 text-sm text-[var(--ink-700)]">{a}</p>
          </article>
        ))}
      </div>
    </section>
  </MarketingLayout>
);

export default FAQ;
