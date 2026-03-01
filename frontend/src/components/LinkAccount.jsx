import { useState } from 'react'
import { registerPlayer, linkAccountByCode } from '../api/supabase'

export default function LinkAccount({ platform, platformUserId, firstName, lastName, onLinked }) {
  const [mode, setMode] = useState(null) // null | 'link' | 'register'
  const [code, setCode] = useState('')
  const [name, setName] = useState([firstName, lastName].filter(Boolean).join(' '))
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLink = async () => {
    if (!code.trim() || code.trim().length !== 6) {
      setError('Введите 6-значный код')
      return
    }
    setLoading(true)
    setError('')
    try {
      const player = await linkAccountByCode(code.trim(), platform, platformUserId)
      onLinked?.(player)
    } catch (e) {
      setError(e?.message || 'Ошибка привязки')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!name.trim()) {
      setError('Введите имя')
      return
    }
    setLoading(true)
    setError('')
    try {
      const player = await registerPlayer(platform, platformUserId, name.trim())
      onLinked?.(player)
    } catch (e) {
      setError(e?.message || 'Ошибка регистрации')
    } finally {
      setLoading(false)
    }
  }

  if (!mode) {
    return (
      <div className="p-4 min-w-[320px] max-w-lg mx-auto">
        <h1 className="text-xl font-bold mb-2">🏓 Лига настольного тенниса</h1>
        <p className="text-[var(--app-hint)] mb-6">
          Добро пожаловать! Выберите, как продолжить:
        </p>
        <div className="flex flex-col gap-3">
          <button
            type="button"
            onClick={() => setMode('link')}
            className="w-full py-4 px-4 rounded-xl text-left border border-[var(--app-hint)]/30"
            style={{ background: 'var(--app-secondary-bg)' }}
          >
            <p className="font-semibold mb-1">Я уже играю в лиге</p>
            <p className="text-sm text-[var(--app-hint)]">
              Привязать аккаунт по коду из Telegram-бота
            </p>
          </button>
          <button
            type="button"
            onClick={() => setMode('register')}
            className="w-full py-4 px-4 rounded-xl text-left border border-[var(--app-hint)]/30"
            style={{ background: 'var(--app-secondary-bg)' }}
          >
            <p className="font-semibold mb-1">Я новый участник</p>
            <p className="text-sm text-[var(--app-hint)]">
              Зарегистрироваться в лиге
            </p>
          </button>
        </div>
      </div>
    )
  }

  if (mode === 'link') {
    return (
      <div className="p-4 min-w-[320px] max-w-lg mx-auto">
        <h1 className="text-xl font-bold mb-2">🔗 Привязка аккаунта</h1>
        <p className="text-sm text-[var(--app-hint)] mb-4">
          Напишите <code>/link</code> боту в Telegram, чтобы получить 6-значный код. Введите его ниже.
        </p>
        <input
          type="text"
          inputMode="numeric"
          maxLength={6}
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
          placeholder="000000"
          className="w-full py-3 px-4 rounded-xl text-center text-2xl tracking-[0.5em] font-mono border border-[var(--app-hint)]/30 mb-4"
          style={{ background: 'var(--app-secondary-bg)', color: 'var(--app-text)' }}
        />
        {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => { setMode(null); setError('') }}
            className="flex-1 py-3 rounded-xl border border-[var(--app-hint)]/40"
          >
            Назад
          </button>
          <button
            type="button"
            onClick={handleLink}
            disabled={loading || code.length !== 6}
            className="flex-1 py-3 rounded-xl font-medium disabled:opacity-50"
            style={{ background: 'var(--app-accent)', color: 'var(--app-accent-text)' }}
          >
            {loading ? 'Проверка...' : 'Привязать'}
          </button>
        </div>
      </div>
    )
  }

  // mode === 'register'
  return (
    <div className="p-4 min-w-[320px] max-w-lg mx-auto">
      <h1 className="text-xl font-bold mb-2">📝 Регистрация</h1>
      <p className="text-sm text-[var(--app-hint)] mb-4">
        Введите ваше имя для отображения в лиге.
      </p>
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Имя Фамилия"
        className="w-full py-3 px-4 rounded-xl border border-[var(--app-hint)]/30 mb-4"
        style={{ background: 'var(--app-secondary-bg)', color: 'var(--app-text)' }}
      />
      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => { setMode(null); setError('') }}
          className="flex-1 py-3 rounded-xl border border-[var(--app-hint)]/40"
        >
          Назад
        </button>
        <button
          type="button"
          onClick={handleRegister}
          disabled={loading || !name.trim()}
          className="flex-1 py-3 rounded-xl font-medium disabled:opacity-50"
          style={{ background: 'var(--app-accent)', color: 'var(--app-accent-text)' }}
        >
          {loading ? 'Регистрация...' : 'Зарегистрироваться'}
        </button>
      </div>
    </div>
  )
}
