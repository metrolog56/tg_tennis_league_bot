import { RESPECT_EMOJI } from '../constants/respect'

const EMOJI_REPEAT = 32

export default function RespectTicker() {
  const line = Array.from({ length: EMOJI_REPEAT }, () => RESPECT_EMOJI).join(' ')

  return (
    <div className="glass-card respect-ticker mb-3 px-3 py-2">
      <div className="respect-ticker-inner" aria-hidden="true">
        <span>{line}</span>
        <span>{line}</span>
      </div>
      <span className="sr-only">Уважение в лиге</span>
    </div>
  )
}

