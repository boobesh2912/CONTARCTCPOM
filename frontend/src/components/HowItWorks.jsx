import MarketingLayout from './MarketingLayout';

const steps = [
  ['1. Capture', 'Record 20-30 seconds or upload a clear voice sample.'],
  ['2. Analyze', 'Backend extracts features like jitter, shimmer, HNR, and F0.'],
  ['3. Score', 'Model computes risk score + confidence and recommendations.'],
  ['4. Track', 'Results are stored and shown in your dashboard trend history.'],
];

const HowItWorks = () => (
  <MarketingLayout>
    <section className="mx-auto max-w-5xl px-4 py-14 sm:px-6 lg:px-8">
      <h1 className="font-display text-4xl font-bold">How It Works</h1>
      <p className="mt-4 text-[var(--ink-700)]">A straightforward workflow built for repeated screening and monitoring.</p>
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        {steps.map(([title, body]) => (
          <article key={title} className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-5 shadow-soft">
            <h3 className="font-display text-xl font-bold">{title}</h3>
            <p className="mt-2 text-sm text-[var(--ink-700)]">{body}</p>
          </article>
        ))}
      </div>
    </section>
  </MarketingLayout>
);

export default HowItWorks;
