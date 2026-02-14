import AppShell from './AppShell';
import { BookOpen, PlayCircle, Timer, HeartPulse, Accessibility, Sparkles, CheckCircle2, CalendarClock } from 'lucide-react';

const videos = [
  {
    title: 'Parkinson\'s Awareness & Guidance',
    description: 'Educational overview and practical understanding of progression and support.',
    videoId: '8fMnIxV-8PY',
  },
  {
    title: 'Neurological Care & Management',
    description: 'Clinical perspective on care planning and risk management steps.',
    videoId: 'OZ9VV9iMTZw',
  },
  {
    title: 'Voice and Daily Function Support',
    description: 'Supportive routines for voice, speech, and everyday communication.',
    videoId: 'riTM_HoWl1k',
  },
];

const pathways = [
  {
    title: 'Week 1: Baseline Awareness',
    focus: 'Learn symptoms and establish a daily voice routine.',
    checklist: ['Read Disease Basics module', 'Complete 3 guided voice warmups', 'Record 1 baseline screening'],
  },
  {
    title: 'Week 2: Movement + Speech',
    focus: 'Pair mobility drills with breath-supported speech.',
    checklist: ['Perform mobility drill 4 times', 'Do sustained-vowel exercise daily', 'Review trend dashboard once'],
  },
  {
    title: 'Week 3+: Trend Tracking',
    focus: 'Interpret changes and prepare clinician questions.',
    checklist: ['Review weekly changes', 'Write top 3 observations', 'Book specialist consultation if risk rises'],
  },
];

const exercises = [
  {
    icon: Accessibility,
    name: 'Seated Posture Reset',
    duration: '5 min',
    frequency: '2x daily',
    steps: [
      'Sit with feet flat and spine tall.',
      'Gently pull shoulders back and down.',
      'Hold for 10 seconds, relax, and repeat 8 times.',
    ],
    tip: 'Keep chin parallel to floor; avoid leaning forward.',
  },
  {
    icon: HeartPulse,
    name: 'Breathing + Voice Warmup',
    duration: '7 min',
    frequency: 'Daily',
    steps: [
      'Inhale through nose for 4 seconds.',
      'Exhale slowly while saying sustained "aaah".',
      'Repeat 10 rounds with consistent volume.',
    ],
    tip: 'Focus on steady breath, not loudness.',
  },
  {
    icon: Timer,
    name: 'Sit-to-Stand Mobility Drill',
    duration: '6 min',
    frequency: '1-2x daily',
    steps: [
      'Sit at edge of chair, feet hip-width apart.',
      'Stand up without using hands if safe.',
      'Sit down slowly; repeat 8-12 reps.',
    ],
    tip: 'Keep movement controlled and symmetrical.',
  },
];

const cardClass = 'rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-5 shadow-soft';

const Learning = ({ user, onLogout }) => {
  return (
    <AppShell
      user={user}
      onLogout={onLogout}
      title="Learning & Exercise"
      subtitle="Understand Parkinson\'s risk factors and practice simple daily routines to support voice, posture, and mobility."
    >
      <div className="space-y-6">
        <section className={cardClass}>
          <div className="mb-4 flex items-center gap-2">
            <CalendarClock className="h-5 w-5 text-[var(--brand-700)]" />
            <h2 className="font-display text-xl font-bold">Guided Learning Path</h2>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            {pathways.map((path) => (
              <article key={path.title} className="rounded-xl border border-[var(--line)] bg-white p-4">
                <h3 className="font-display text-lg font-bold">{path.title}</h3>
                <p className="mt-1 text-sm text-[var(--ink-700)]">{path.focus}</p>
                <ul className="mt-3 space-y-2">
                  {path.checklist.map((item) => (
                    <li key={item} className="flex items-start gap-2 text-sm text-[var(--ink-700)]">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[var(--brand-700)]" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section className={cardClass}>
          <div className="mb-4 flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-[var(--brand-700)]" />
            <h2 className="font-display text-xl font-bold">Learning Modules</h2>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <article className="rounded-xl bg-[var(--bg-2)] p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-600)]">Module 01</p>
              <h3 className="mt-1 font-display text-lg font-bold">Disease Basics</h3>
              <p className="mt-2 text-sm text-[var(--ink-700)]">What Parkinson\'s is, key symptoms, and when to seek evaluation.</p>
            </article>
            <article className="rounded-xl bg-[var(--bg-2)] p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-600)]">Module 02</p>
              <h3 className="mt-1 font-display text-lg font-bold">Prevention Habits</h3>
              <p className="mt-2 text-sm text-[var(--ink-700)]">Sleep, physical activity, and speech practice routines.</p>
            </article>
            <article className="rounded-xl bg-[var(--bg-2)] p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-600)]">Module 03</p>
              <h3 className="mt-1 font-display text-lg font-bold">Action Plan</h3>
              <p className="mt-2 text-sm text-[var(--ink-700)]">How to use screening trends and prepare clinician questions.</p>
            </article>
          </div>
        </section>

        <section className={cardClass}>
          <div className="mb-4 flex items-center gap-2">
            <PlayCircle className="h-5 w-5 text-[var(--brand-700)]" />
            <h2 className="font-display text-xl font-bold">Video Resources</h2>
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            {videos.map((video) => (
              <article key={video.videoId} className="overflow-hidden rounded-xl border border-[var(--line)] bg-white">
                <div className="aspect-video">
                  <iframe
                    className="h-full w-full"
                    src={`https://www.youtube.com/embed/${video.videoId}`}
                    title={video.title}
                    loading="lazy"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    referrerPolicy="strict-origin-when-cross-origin"
                    allowFullScreen
                  />
                </div>
                <div className="p-4">
                  <h3 className="font-display text-lg font-bold text-[var(--ink-900)]">{video.title}</h3>
                  <p className="mt-1 text-sm text-[var(--ink-700)]">{video.description}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className={cardClass}>
          <div className="mb-4 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-[var(--brand-700)]" />
            <h2 className="font-display text-xl font-bold">Daily Exercise Coach</h2>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            {exercises.map((exercise) => {
              const Icon = exercise.icon;
              return (
                <article key={exercise.name} className="rounded-xl border border-[var(--line)] bg-white p-4">
                  <div className="mb-3 flex items-start justify-between">
                    <div>
                      <h3 className="font-display text-lg font-bold">{exercise.name}</h3>
                      <p className="text-xs text-[var(--ink-600)]">{exercise.duration} | {exercise.frequency}</p>
                    </div>
                    <Icon className="h-5 w-5 text-[var(--brand-700)]" />
                  </div>

                  <div className="exercise-figure-wrap mb-3">
                    <div className="exercise-figure">
                      <span className="exercise-head" />
                      <span className="exercise-body" />
                      <span className="exercise-arm exercise-arm-left" />
                      <span className="exercise-arm exercise-arm-right" />
                      <span className="exercise-leg exercise-leg-left" />
                      <span className="exercise-leg exercise-leg-right" />
                    </div>
                  </div>

                  <ol className="space-y-1 text-sm text-[var(--ink-700)]">
                    {exercise.steps.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>

                  <p className="mt-3 rounded-lg bg-[var(--bg-2)] px-3 py-2 text-xs text-[var(--ink-700)]">
                    Tip: {exercise.tip}
                  </p>
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </AppShell>
  );
};

export default Learning;
