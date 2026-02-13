import MarketingLayout from './MarketingLayout';

const Pricing = () => (
  <MarketingLayout>
    <section className="mx-auto max-w-5xl px-4 py-14 sm:px-6 lg:px-8">
      <h1 className="font-display text-4xl font-bold">Pricing</h1>
      <div className="mt-8 grid gap-5 md:grid-cols-2">
        <article className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-6 shadow-soft">
          <h2 className="font-display text-2xl font-bold">Starter</h2>
          <p className="mt-2 text-3xl font-bold">$0<span className="text-base font-medium"> / month</span></p>
          <ul className="mt-4 space-y-2 text-sm text-[var(--ink-700)]">
            <li>- 3 tests / month</li>
            <li>- Basic dashboard history</li>
            <li>- Standard support</li>
          </ul>
        </article>
        <article className="rounded-2xl border border-[var(--line)] bg-[var(--ink-900)] p-6 text-white shadow-soft">
          <h2 className="font-display text-2xl font-bold">Pro</h2>
          <p className="mt-2 text-3xl font-bold">$9<span className="text-base font-medium"> / month</span></p>
          <ul className="mt-4 space-y-2 text-sm text-white/90">
            <li>- Unlimited tests</li>
            <li>- Full trend tracking</li>
            <li>- Priority support</li>
          </ul>
        </article>
      </div>
    </section>
  </MarketingLayout>
);

export default Pricing;
