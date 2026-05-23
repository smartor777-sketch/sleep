// Inline pill recorder for compose. Records via MediaRecorder, uploads via api.transcribe.
import { useEffect, useRef, useState } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';
import { api } from '../lib/api';
import clsx from 'clsx';

interface Props {
  onText: (text: string) => void;
  disabled?: boolean;
}

export default function AudioButton({ onText, disabled }: Props) {
  const [recording, setRecording] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => () => stopStream(), []);

  function stopStream() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }

  async function start() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : '';
      const rec = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };
      rec.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: mime || 'audio/webm' });
        stopStream();
        setRecording(false);
        if (blob.size < 200) return;
        setUploading(true);
        try {
          const r = await api.transcribe(blob);
          if (r.text) onText(r.text);
        } catch (e: any) {
          setError(e?.detail || 'Не удалось распознать');
        } finally {
          setUploading(false);
        }
      };
      recRef.current = rec;
      rec.start();
      setRecording(true);
    } catch (e: any) {
      setError('Нет доступа к микрофону');
    }
  }

  function stop() {
    recRef.current?.stop();
  }

  const busy = recording || uploading;

  return (
    <button
      type="button"
      onClick={busy ? stop : start}
      disabled={disabled || uploading}
      data-testid="audio-record-btn"
      title={recording ? 'Остановить запись' : 'Голосовой ввод'}
      className={clsx(
        'w-11 h-11 rounded-full flex items-center justify-center transition-all',
        recording
          ? 'bg-red-500/90 text-white animate-pulse-soft'
          : uploading
          ? 'bg-white/8 text-white/70'
          : 'accent-bg text-white hover:opacity-90'
      )}
    >
      {uploading ? <Loader2 className="w-5 h-5 animate-spin" /> :
        recording ? <Square className="w-4 h-4" /> :
        <Mic className="w-5 h-5" />}
      {error && (
        <span className="sr-only" data-testid="audio-error">{error}</span>
      )}
    </button>
  );
}
