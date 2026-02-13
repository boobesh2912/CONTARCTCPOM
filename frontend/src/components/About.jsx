import MarketingLayout from './MarketingLayout';

const About = () => (
  <MarketingLayout>
    <section className="mx-auto max-w-4xl px-4 py-14 sm:px-6 lg:px-8">
      <h1 className="font-display text-4xl font-bold">About MediGuardian</h1>
      <p className="mt-4 text-[var(--ink-700)]">
        MediGuardian is a voice-screening micro-SaaS focused on early Parkinson's risk indication. It helps users run recurring voice tests and monitor trend changes over time.
      </p>
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <article className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-5 shadow-soft"><h3 className="font-display text-lg font-bold">Mission</h3><p className="mt-2 text-sm text-[var(--ink-700)]">Make early screening accessible and repeatable.</p></article>
        <article className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-5 shadow-soft"><h3 className="font-display text-lg font-bold">Approach</h3><p className="mt-2 text-sm text-[var(--ink-700)]">Voice biomarkers + ML inference + historical tracking.</p></article>
        <article className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-5 shadow-soft"><h3 className="font-display text-lg font-bold">Disclaimer</h3><p className="mt-2 text-sm text-[var(--ink-700)]">Screening support only, not medical diagnosis.</p></article>
      </div>
    </section>
  </MarketingLayout>
);

export default About;
