import { useEffect, useRef } from 'react'
import { getScenarioReaction } from '../utils/matchScenario'

const CARD_W = 600
const CARD_H = 340
const SCALE = 2 // retina

function formatDelta(delta) {
  if (delta == null) return '—'
  const n = Number(delta)
  if (isNaN(n)) return '—'
  return n >= 0 ? `+${n.toFixed(2)}` : n.toFixed(2)
}

function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = text.split(' ')
  let line = ''
  let currentY = y
  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + ' '
    if (ctx.measureText(testLine).width > maxWidth && n > 0) {
      ctx.fillText(line.trim(), x, currentY)
      line = words[n] + ' '
      currentY += lineHeight
    } else {
      line = testLine
    }
  }
  ctx.fillText(line.trim(), x, currentY)
  return currentY
}

/**
 * Отрисовывает карточку результата матча на Canvas.
 *
 * @param {HTMLCanvasElement} canvas
 * @param {object} data
 * @param {string}  data.scenario        - ключ сценария из SCENARIOS
 * @param {string}  data.player1Name
 * @param {string}  data.player2Name
 * @param {number}  data.player1Position
 * @param {number}  data.player2Position
 * @param {number}  data.sets1           - сеты player1
 * @param {number}  data.sets2           - сеты player2
 * @param {number}  data.delta1          - изменение рейтинга player1
 * @param {number}  data.delta2          - изменение рейтинга player2
 * @param {string}  data.divisionName
 * @param {string}  data.seasonName
 */
function drawCard(canvas, data) {
  const ctx = canvas.getContext('2d')
  const w = CARD_W * SCALE
  const h = CARD_H * SCALE
  canvas.width = w
  canvas.height = h
  ctx.scale(SCALE, SCALE)

  const reaction = getScenarioReaction(data.scenario)
  const [colorStart, colorEnd] = reaction.gradient

  // Background gradient
  const grad = ctx.createLinearGradient(0, 0, CARD_W, CARD_H)
  grad.addColorStop(0, colorStart)
  grad.addColorStop(1, colorEnd)
  ctx.fillStyle = grad
  ctx.beginPath()
  ctx.roundRect(0, 0, CARD_W, CARD_H, 18)
  ctx.fill()

  // Subtle noise overlay
  ctx.fillStyle = 'rgba(255,255,255,0.04)'
  for (let i = 0; i < CARD_W; i += 4) {
    for (let j = 0; j < CARD_H; j += 4) {
      if (Math.random() > 0.6) ctx.fillRect(i, j, 2, 2)
    }
  }

  // Top header line: division · season
  ctx.fillStyle = 'rgba(255,255,255,0.55)'
  ctx.font = '500 14px system-ui, sans-serif'
  ctx.textAlign = 'center'
  const headerText = [data.divisionName, data.seasonName].filter(Boolean).join(' · ')
  ctx.fillText(headerText, CARD_W / 2, 32)

  // Emoji + reaction headline
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 26px system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(`${reaction.emoji}  ${reaction.headline}`, CARD_W / 2, 74)

  // Subline
  ctx.fillStyle = 'rgba(255,255,255,0.70)'
  ctx.font = '400 14px system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(reaction.subline, CARD_W / 2, 96)

  // ---- Players row ----
  const playerRowY = 160
  const cx = CARD_W / 2

  // Score (center)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 52px system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(`${data.sets1}  :  ${data.sets2}`, cx, playerRowY + 8)

  // Player 1 (left)
  const p1Won = data.sets1 > data.sets2
  drawPlayerBlock(ctx, {
    name: data.player1Name,
    position: data.player1Position,
    delta: data.delta1,
    x: 100,
    y: playerRowY,
    align: 'center',
    isWinner: p1Won,
  })

  // Player 2 (right)
  drawPlayerBlock(ctx, {
    name: data.player2Name,
    position: data.player2Position,
    delta: data.delta2,
    x: CARD_W - 100,
    y: playerRowY,
    align: 'center',
    isWinner: !p1Won,
  })

  // Divider line
  ctx.strokeStyle = 'rgba(255,255,255,0.15)'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(32, 240)
  ctx.lineTo(CARD_W - 32, 240)
  ctx.stroke()

  // Footer: rating deltas
  ctx.fillStyle = 'rgba(255,255,255,0.55)'
  ctx.font = '400 13px system-ui, sans-serif'
  ctx.textAlign = 'left'
  const d1Text = `${data.player1Name.split(' ')[0]}  ${formatDelta(data.delta1)} очков`
  const d2Text = `${formatDelta(data.delta2)} очков  ${data.player2Name.split(' ')[0]}`
  ctx.fillText(d1Text, 36, 264)
  ctx.textAlign = 'right'
  ctx.fillText(d2Text, CARD_W - 36, 264)

  // League watermark
  ctx.fillStyle = 'rgba(255,255,255,0.40)'
  ctx.font = '500 13px system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('🤝 MI Tennis League', cx, CARD_H - 18)
}

function drawPlayerBlock(ctx, { name, position, delta, x, y, align, isWinner }) {
  // Position badge
  if (position) {
    const badgeX = x
    const badgeY = y - 52
    ctx.fillStyle = isWinner ? 'rgba(255,255,255,0.25)' : 'rgba(255,255,255,0.12)'
    ctx.beginPath()
    ctx.roundRect(badgeX - 22, badgeY - 16, 44, 24, 6)
    ctx.fill()
    ctx.fillStyle = 'rgba(255,255,255,0.85)'
    ctx.font = 'bold 12px system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(`#${position}`, badgeX, badgeY)
  }

  // Player name
  ctx.fillStyle = isWinner ? '#ffffff' : 'rgba(255,255,255,0.75)'
  ctx.font = isWinner ? 'bold 16px system-ui, sans-serif' : '400 15px system-ui, sans-serif'
  ctx.textAlign = 'center'
  const shortName = name.length > 14 ? name.slice(0, 13) + '…' : name
  ctx.fillText(shortName, x, y + 38)
}

/**
 * Модальная карточка с результатом матча.
 *
 * Props:
 *   data     {object}   — данные карточки (см. drawCard)
 *   onClose  {function} — закрыть
 */
export default function MatchResultCard({ data, onClose }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    if (canvasRef.current && data) {
      drawCard(canvasRef.current, data)
    }
  }, [data])

  const handleDownload = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const link = document.createElement('a')
    link.download = 'match-result.png'
    link.href = canvas.toDataURL('image/png')
    link.click()
  }

  if (!data) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.7)' }}
      onClick={onClose}
    >
      <div
        className="flex flex-col items-center gap-4 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <canvas
          ref={canvasRef}
          style={{
            width: '100%',
            borderRadius: 12,
            display: 'block',
          }}
        />
        <div className="flex gap-3 w-full">
          <button
            type="button"
            onClick={handleDownload}
            className="flex-1 py-3 rounded-xl font-medium text-white"
            style={{ background: 'rgba(255,255,255,0.18)' }}
          >
            ⬇ Сохранить
          </button>
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-3 rounded-xl font-medium text-white"
            style={{ background: 'rgba(255,255,255,0.12)' }}
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  )
}
