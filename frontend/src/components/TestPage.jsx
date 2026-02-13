import { useEffect, useRef, useState } from 'react';
import { AlertCircle, CheckCircle2, Loader2, Mic, Square, UploadCloud } from 'lucide-react';
import AppShell from './AppShell';
import { analysisAPI, getImageUrl } from '../api';

const panelClass = 'rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-5 shadow-soft';

function riskTone(score) {
  if (score < 30) return { badge: 'Low Concern', text: 'text-emerald-700', bg: 'bg-emerald-100' };
  if (score < 60) return { badge: 'Moderate Concern', text: 'text-amber-700', bg: 'bg-amber-100' };
  return { badge: 'High Concern', text: 'text-rose-700', bg: 'bg-rose-100' };
}

function encodeWav(audioBuffer) {
  const channelData = audioBuffer.getChannelData(0);
  const sampleRate = audioBuffer.sampleRate;
  const dataLength = channelData.length * 2;
  const buffer = new ArrayBuffer(44 + dataLength);
  const view = new DataView(buffer);

  const writeString = (offset, str) => {
    for (let i = 0; i < str.length; i += 1) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + dataLength, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, dataLength, true);

  let offset = 44;
  for (let i = 0; i < channelData.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, channelData[i]));
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
    offset += 2;
  }

  return new Blob([view], { type: 'audio/wav' });
}

async function convertBlobToWav(blob) {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  try {
    const arrayBuffer = await blob.arrayBuffer();
    const decoded = await audioContext.decodeAudioData(arrayBuffer.slice(0));
    return encodeWav(decoded);
  } finally {
    await audioContext.close();
  }
}

const TestPage = ({ user, onLogout }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [audioFile, setAudioFile] = useState(null);

  const timerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const analyzeRecording = async (file) => {
    const input = file || audioFile;
    if (!input) {
      setError('Please record or upload an audio file first.');
      return;
    }

    setIsAnalyzing(true);
    setError('');

    try {
      const response = await analysisAPI.analyzeAudio(input);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const preferredTypes = [
        'audio/webm;codecs=opus',
        'audio/ogg;codecs=opus',
        'audio/webm',
      ];
      const selectedMimeType = preferredTypes.find((type) => MediaRecorder.isTypeSupported(type));
      const mediaRecorder = selectedMimeType
        ? new MediaRecorder(stream, { mimeType: selectedMimeType })
        : new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      setAudioFile(null);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        try {
          const sourceBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType || 'audio/webm' });
          const wavBlob = await convertBlobToWav(sourceBlob);
          const file = new File([wavBlob], `recording-${Date.now()}.wav`, { type: 'audio/wav' });
          setAudioFile(file);
        } catch {
          setError('Recorded audio conversion failed. Please use upload for this browser/device.');
        } finally {
          stream.getTracks().forEach((track) => track.stop());
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      setError('');

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          if (prev >= 29) {
            stopRecording();
            return 30;
          }
          return prev + 1;
        });
      }, 1000);
    } catch {
      setError('Microphone access denied. Please allow microphone permission and try again.');
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
    if (mediaRecorderRef.current?.state === 'recording') mediaRecorderRef.current.stop();
  };

  const handleFileUpload = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setAudioFile(file);
    setError('');
  };

  const resetTest = () => {
    setResult(null);
    setAudioFile(null);
    setError('');
    setRecordingTime(0);
    setIsRecording(false);
  };

  const tone = result ? riskTone(result.risk_score) : null;

  return (
    <AppShell
      user={user}
      onLogout={onLogout}
      title="Voice Assessment Lab"
      subtitle="Capture a 30-second sample, run the model, and review interpretable voice biomarkers instantly."
    >
      {isAnalyzing ? (
        <section className={`${panelClass} text-center`}>
          <Loader2 className="mx-auto h-12 w-12 animate-spin text-[var(--brand-700)]" />
          <h2 className="mt-4 font-display text-2xl font-bold text-[var(--ink-900)]">Analyzing Voice Biomarkers</h2>
          <p className="mt-2 text-sm text-[var(--ink-700)]">This usually takes 5-20 seconds depending on file length.</p>
        </section>
      ) : result ? (
        <div className="space-y-6">
          <section className={`${panelClass} text-center`}>
            <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${tone.bg} ${tone.text}`}>{tone.badge}</span>
            <h2 className="mt-3 font-display text-3xl font-bold text-[var(--ink-900)]">Risk Score: {result.risk_score}%</h2>
            <p className="mt-1 text-sm text-[var(--ink-700)]">Confidence: {Math.round(result.confidence * 100)}%</p>
            <div className="mx-auto mt-4 h-2 max-w-xl rounded-full bg-[var(--bg-2)]">
              <div className="h-2 rounded-full bg-[var(--ink-900)]" style={{ width: `${Math.round(result.confidence * 100)}%` }} />
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-4">
            <div className={panelClass}><p className="text-xs text-[var(--ink-600)]">Jitter</p><p className="font-display text-2xl font-bold">{result.features.jitter_relative.toFixed(4)}</p></div>
            <div className={panelClass}><p className="text-xs text-[var(--ink-600)]">Shimmer</p><p className="font-display text-2xl font-bold">{result.features.shimmer_relative.toFixed(4)}</p></div>
            <div className={panelClass}><p className="text-xs text-[var(--ink-600)]">HNR (dB)</p><p className="font-display text-2xl font-bold">{result.features.hnr.toFixed(2)}</p></div>
            <div className={panelClass}><p className="text-xs text-[var(--ink-600)]">F0 Mean (Hz)</p><p className="font-display text-2xl font-bold">{result.features.f0_mean.toFixed(1)}</p></div>
          </section>

          <section className="grid gap-4 md:grid-cols-2">
            <article className={panelClass}>
              <h3 className="mb-3 font-display text-lg font-bold">Waveform</h3>
              <img src={getImageUrl(result.visualizations.waveform_url)} alt="Waveform" className="w-full rounded-xl border border-[var(--line)]" />
            </article>
            <article className={panelClass}>
              <h3 className="mb-3 font-display text-lg font-bold">Spectrogram</h3>
              <img src={getImageUrl(result.visualizations.spectrogram_url)} alt="Spectrogram" className="w-full rounded-xl border border-[var(--line)]" />
            </article>
          </section>

          <section className={panelClass}>
            <h3 className="mb-3 font-display text-lg font-bold text-[var(--ink-900)]">Recommendations</h3>
            <ul className="space-y-2">
              {result.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-[var(--ink-800)]">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 text-[var(--brand-700)]" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <button onClick={resetTest} className="rounded-full border border-[var(--line)] bg-white px-5 py-2 text-sm font-semibold">Run New Test</button>
              <button onClick={() => (window.location.href = '/dashboard')} className="rounded-full bg-[var(--ink-900)] px-5 py-2 text-sm font-semibold text-white">Back to Overview</button>
            </div>
          </section>
        </div>
      ) : (
        <div className="space-y-6">
          <section className={panelClass}>
            <div className="grid gap-6 lg:grid-cols-2">
              <div>
                <h2 className="font-display text-2xl font-bold text-[var(--ink-900)]">Record Live Sample</h2>
                <p className="mt-2 text-sm text-[var(--ink-700)]">Speak naturally for up to 30 seconds in a quiet room.</p>
                <div className="mt-6 flex items-center gap-4">
                  <div className={`flex h-24 w-24 items-center justify-center rounded-full ${isRecording ? 'bg-rose-100' : 'bg-[var(--brand-100)]'}`}>
                    <Mic className={`h-10 w-10 ${isRecording ? 'recording-pulse text-rose-600' : 'text-[var(--brand-700)]'}`} />
                  </div>
                  <div>
                    <p className="font-display text-4xl font-bold text-[var(--ink-900)]">{recordingTime}s</p>
                    <p className="text-xs text-[var(--ink-600)]">{isRecording ? 'Recording in progress' : 'Not recording'}</p>
                  </div>
                </div>
                <div className="mt-6 flex flex-wrap gap-3">
                  {!isRecording ? (
                    <button onClick={startRecording} className="inline-flex items-center gap-2 rounded-full bg-[var(--ink-900)] px-5 py-2 text-sm font-semibold text-white">
                      <Mic className="h-4 w-4" /> Start
                    </button>
                  ) : (
                    <button onClick={stopRecording} className="inline-flex items-center gap-2 rounded-full bg-rose-600 px-5 py-2 text-sm font-semibold text-white">
                      <Square className="h-4 w-4" /> Stop
                    </button>
                  )}
                  <button
                    onClick={() => analyzeRecording()}
                    disabled={!audioFile}
                    className="rounded-full border border-[var(--line)] bg-white px-5 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Analyze Sample
                  </button>
                </div>
              </div>

              <div className="rounded-2xl border border-dashed border-[var(--line)] bg-[var(--bg-2)] p-6">
                <h3 className="font-display text-lg font-bold text-[var(--ink-900)]">Or Upload Audio</h3>
                <p className="mt-2 text-sm text-[var(--ink-700)]">Accepted: WAV, MP3, OGG, FLAC, M4A</p>
                <label className="mt-4 flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-[var(--line)] bg-white px-4 py-3 text-sm font-semibold text-[var(--ink-800)]">
                  <UploadCloud className="h-4 w-4" />
                  <span>{audioFile ? audioFile.name : 'Choose file'}</span>
                  <input type="file" accept="audio/*" className="hidden" onChange={handleFileUpload} />
                </label>
                <ul className="mt-5 space-y-2 text-xs text-[var(--ink-700)]">
                  <li>- Keep mouth 6-8 inches from microphone.</li>
                  <li>- Avoid fans/background TV noise.</li>
                  <li>- Use normal speaking pace and volume.</li>
                </ul>
              </div>
            </div>
          </section>

          {error && (
            <section className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
              <AlertCircle className="mt-0.5 h-4 w-4" />
              <span>{error}</span>
            </section>
          )}
        </div>
      )}
    </AppShell>
  );
};

export default TestPage;
